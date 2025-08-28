import os
import shutil
import argparse
import json
import re
import logging
import logging.handlers
import io
from importlib import import_module

import pandas as pd

from iodp import utils


def configure_logging(outdir:str=None):
    
    outfile = 'sodlab.log'

    if outdir:
        if not os.path.exists(outdir):
            raise FileNotFoundError(f'Logging directory does not exist at: {outdir}')
        outfile = os.path.normpath(os.path.join(outdir, outfile))
    else:
        # get location of where this script is running:
        path = os.path.dirname(os.path.abspath(__file__))
        outfile = os.path.normpath(os.path.join(path, outfile))
        
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.handlers.RotatingFileHandler(outfile, 
                                                mode="a",
                                                maxBytes = 50 * (1024)**2,
                                                backupCount=5,
                                                encoding='utf-8')
            ]
        )
    
    print("")
    print(f"Logs will be written to: {outfile}")
    print("")

# NOTE: The configuration for this logger is set in main()
logger = logging.getLogger(__name__)

class DataLoader:
    """Class to handle archiving and transforming raw data files from SOD track systems controlled by IMS.
    """
    def __init__(
        self,
        path: str,
        analysis: str,
        output_dir: str,
        recursive: bool = False,
        force:bool = False,
        settings:str=None,
    ):

        self.path = path
        self._recursive = recursive
        self.analysis = analysis
        self._force = force
        self._settings = settings

        # Check if path and output_dir are on the same drive
        # Hard-linked files can only exist on same volume.
        # path_drive = os.path.splitdrive(os.path.abspath(path))[0]
        # output_drive = os.path.splitdrive(os.path.abspath(output_dir))[0]
        # if path_drive and output_drive and path_drive.lower() != output_drive.lower():
        #     raise ValueError(f"Source path '{path}' and output directory '{output_dir}' are not on the same drive.")

        # TODO: Use dictionary get commands to verify keys exist
        self.graph =  self._settings["systems"][self.analysis]

        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            self.output_dir = output_dir
        except Exception as e:
            logger.error(f"Failed to create output directory '{output_dir}': {e}")
            raise

    def get_instrument_files(self):
        
        pattern = rf".+\.{self.analysis}$"
        
        return self._get_files(
            path = self.path,
            pattern = pattern,
            recursive=self._recursive
        )
        
    def get_summary_files(self):
        
        pattern = rf"^summary_{self.analysis.lower()}.+\.json$"

        return self._get_files(
            path = self.output_dir,
            pattern=pattern,
            recursive=True
        )
        
        
    def _get_files(self, path: str, pattern: str, recursive: bool):

        files = None
        reg = None

        # Adjust the lambda to include the regex match if specified.
        try:
            reg = re.compile(pattern)
            predicate = lambda x: reg.match(x)

            path = os.path.normpath(path)

            if not os.path.exists(path):
                raise FileNotFoundError(f"Path does not exist: {path}")

            if recursive:
                files = [
                    os.path.join(root, file)
                    for root, _, files in os.walk(path)
                    for file in files
                    if predicate(file)
                ]
            else:
                files = [
                    os.path.join(path, file)
                    for file in os.listdir(path)
                    if predicate(file)
                ]
        except Exception as e:
            logger.error(e)
            raise

        return files

        
    def archive(self, instrument_file:str, hardlink: True):

        print("")
        GREEN = "\033[92m"
        RESET = "\033[0m"
        logger.info(f"{GREEN}Organizing raw data files for file: {instrument_file}{RESET}")

        if not os.path.isfile(instrument_file):
            logger.error(f"File does not exist: {instrument_file}")
            raise

        inst_filename = os.path.basename(instrument_file)

        # The testid is the root name of the file. It follows a format of TEXTID/SAMPLENAME - DATETIME
        testid, _ = os.path.splitext(inst_filename)

        contents: dict = utils.read_instrument_file(instrument_file, as_dataframe=False)

        raw_files = []

        # all file references are stored in the <FILE></FILE> section
        for file_name_key in self.graph["files"].keys():
            raw_files.append((file_name_key, contents[file_name_key]))

        # location where RDF will be stored for TEST
        analysis_path = os.path.normpath(os.path.join(self.output_dir, self.analysis))
        test_path = os.path.normpath(os.path.join(self.output_dir, self.analysis, testid))
        test_raw_path = os.path.normpath(os.path.join(test_path, "raw"))
        
        
        # check for existence of the summary json
        summary_path = os.path.join(test_path, f"summary_{self.analysis.lower()}_{testid}.json")
        
        summary = {}
        if os.path.exists(summary_path):
            with open(summary_path, 'r') as f:
                summary = json.load(f)
            
        
        summary["raw_files"] = summary.get('raw_files', {})
        summary["testid"] = summary.get('testid',testid)
        summary["analysis"] = summary.get('analysis',self.analysis)
        summary["instrument_file"] = summary.get('instrument_file',instrument_file)

        try:
            os.makedirs(test_raw_path, exist_ok=True)
        except Exception as e:
            logger.error(f"Error creating folder for test {testid}.")
            raise

    
        try:
            # Add instrument file reference to raw files. It must be exported too.
            raw_files.append(("instrument_file", instrument_file))

            # archive the RDF. They will either be hard-links or file copies.
            for file_name_key, file in raw_files:
                summary["raw_files"][file_name_key] = summary['raw_files'].get(file_name_key, {})

                # verify raw file exists at source:
                if not os.path.exists(file):
                    logger.error(
                        f"{file_name_key}: Raw data file does not exist at source: {file}"
                    )
                    continue

                filename = os.path.basename(file)
                new_path = os.path.join(test_raw_path, filename)

                if os.path.exists(new_path):
                    if not self._force:
                        logger.warning(f"{file_name_key}: File already exists at {new_path}. Skipping archiving.")
                        continue
                
                    os.unlink(new_path)

                if hardlink:
                    os.link(file, new_path)
                    logger.info(f"{file_name_key}: File hard-linked to: {new_path}")

                    summary["raw_files"][file_name_key]["hardlinked"] = str(True)
                else:
                    shutil.copy2(file, new_path)
                    logger.info(f"{file_name_key}: File copied to: {new_path}")

                    summary["raw_files"][file_name_key]["hardlinked"] = str(False)

                summary["raw_files"][file_name_key]["original_path"] = file
                summary["raw_files"][file_name_key]["basename"] = filename
                summary["raw_files"][file_name_key]["relative_path"] = os.path.relpath(new_path, analysis_path)

        except Exception as e:
            logger.error(e)
            logger.error(f"Error creating file archive for test: {testid}")
            raise

         
        with open(summary_path, "w") as f:
            summary_ordered = self._sort_summary(summary)
            json.dump(summary_ordered, f, indent=4)
            logger.info(f"Summary written to: {summary_path}")

    def transform(self, summary_file):
        """Uses the summary file to reference files. Assumes the files exist in a local directory. The summary file is a .json file."""

        # NOTE: The summary file is nested in a test folder.

        summary = None

        if not os.path.isfile(summary_file):
            raise FileNotFoundError(
                f"Test summary file does not exist at: {summary_file}"
            )

        print("")
        GREEN = "\033[92m"
        RESET = "\033[0m"
        logger.info(
            f"{GREEN}Applying transformations for test summary file: {summary_file}{RESET}"
        )

        test_dir = os.path.dirname(summary_file)
        test_parent_dir = os.path.dirname(test_dir)

        with open(summary_file, "r") as f:
            summary = json.load(f)

        summary["transformed_files"] = summary.get('transformed_files',{})

        raw_data_files = summary["raw_files"]

        for file_name_key, rdf in raw_data_files.items():

            # NOTE: relative path starts in a folder named by testid
            src = rdf.get("relative_path", None)

            if src is None:
                logger.info(
                    f"instrument file: {src}, {file_name_key}: Has no file reference."
                )
                continue

            src = os.path.join(test_parent_dir, src)

            summary["transformed_files"][file_name_key] = summary["transformed_files"].get(file_name_key,{})
            summary["transformed_files"][file_name_key]["original_path"] = src
            
            # test if tranformed file already exists
            trans_file = summary["transformed_files"][file_name_key].get("relative_path", None)

            if trans_file and os.path.exists(os.path.join(test_parent_dir, trans_file)):
                if not self._force:
                    logger.warning(f"{file_name_key}: Transformed file already exists at {trans_file}. Skipping transformation.")
                    continue
                

            if file_name_key == "instrument_file":
                transform_func = self.graph["instrument_file"]["func"]
                kwargs = self.graph["instrument_file"]["kwargs"]
                depths_spec = self.graph["instrument_file"].get("add_depths", None)
            else:
                transform_func = self.graph["files"][file_name_key]["func"]
                kwargs = self.graph["files"][file_name_key]["kwargs"]
                depths_spec = self.graph["files"][file_name_key].get("add_depths", None)

            # RDF will exist in the test directory
            if not os.path.isfile(src):
                raise FileNotFoundError(
                    f"{file_name_key}: File does not exist at: {src}"
                )
            
            

            logger.info(f"{file_name_key}: Source file location: {src}")

            if transform_func is None:
                logger.info(f"No transform function specified. Skipping.")
                continue

            logger.info(
                f"{file_name_key}: Transform function: {transform_func.__module__}.{transform_func.__name__}, kwargs: {kwargs}"
            )

            depths_added = False
            try:
                # the variable here may be a range of different data types.
                temp = transform_func(src, **kwargs)

                if isinstance(temp, pd.DataFrame):
                    if depths_spec and depths_spec.get("active", None):
                        depths_added = True
                        temp = utils.add_depths_to_dataframe(
                            df=temp,
                            offset_col=depths_spec.get("offset_col", None),
                            sample_number_col=depths_spec.get(
                                "sample_number_col", None
                            ),
                            is_textid_col=depths_spec.get("is_textid_col", None),
                        )

            except Exception as e:
                logger.error(e)
                logger.error(
                    f"Could not apply transformation to file: {src}. Skipping..."
                )
                continue

            raw_filename_root, ext = os.path.splitext(rdf.get("basename", None))

            # Currently BytesIO are for zip files from the NGR (.zip) and SHIL images (.tiff, .jpg, etc)
            if isinstance(temp, io.BytesIO):
                destination_path = os.path.normpath(
                    os.path.join(test_dir, "transform", raw_filename_root) + ext
                )
                os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                with open(destination_path, "wb") as f:
                    f.write(temp.read())

            elif isinstance(temp, pd.DataFrame):
                # instrument files may have the same name (different extension) as other RDF
                if file_name_key == "instrument_file":
                    destination_path = os.path.normpath(
                        os.path.join(
                            test_dir,
                            "transform",
                            f"instrument_file_{raw_filename_root}",
                        )
                        + ".csv"
                    )
                else:
                    destination_path = os.path.normpath(
                        os.path.join(test_dir, "transform", raw_filename_root) + ".csv"
                    )
                os.makedirs(os.path.dirname(destination_path), exist_ok=True)

                temp.to_csv(destination_path, index=False)

            else:
                logger.error(
                    f"Unspecified output file type for temp file with datatype {type(temp)}. Skipping..."
                )
                continue

            summary["transformed_files"][file_name_key]["basename"] = os.path.split(
                destination_path
            )[-1]
            summary["transformed_files"][file_name_key]["relative_path"] = (
                os.path.relpath(destination_path, test_parent_dir)
            )
            summary["transformed_files"][file_name_key][
                "transform"
            ] = f"{transform_func.__module__}.{transform_func.__name__}"
            summary["transformed_files"][file_name_key]["kwargs"] = kwargs
            summary["transformed_files"][file_name_key]["add_depths"] = depths_added

            logger.info(
                f"{file_name_key}: Transformed file saved to: {destination_path}"
            )

        with open(summary_file, "w") as f:
            summary_ordered = self._sort_summary(summary)
            json.dump(summary_ordered, f, indent=4)
            logger.info(f"Summary written to: {summary_file}")


    def _sort_summary(self, dict: dict):
        """Sorts the summary dictionary in a pre-defined key ordering.

        Args:
            dict (dict): _description_

        Returns:
            _type_: _description_
        """

        key_order = [
            "analysis",
            "testid",
            "instrument_file",
            "raw_files",
            "transformed_files",
        ]

        sorted_dict = {k: dict[k] for k in key_order if k in dict}

        return sorted_dict

def resolve_function(func_path: str):
    """Convert 'module.func' string into a function reference."""
    module_name, func_name = func_path.rsplit(".", 1)
    module = import_module(module_name)
    return getattr(module, func_name)


def recursively_resolve_funcs(obj):
    """Recursively resolve any 'func' keys that contain a string path."""
    if isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            if k == "func" and isinstance(v, str):
                new_dict[k] = resolve_function(v)
            else:
                new_dict[k] = recursively_resolve_funcs(v)
        return new_dict
    elif isinstance(obj, list):
        return [recursively_resolve_funcs(item) for item in obj]
    else:
        return convert_bool_value(obj)


def convert_bool_value(value):
    """Convert string booleans to actual bools."""
    if isinstance(value, str):
        lower = value.strip().lower()
        if lower == "true":
            return True
        elif lower == "false":
            return False
    return value


def main():

    parser = argparse.ArgumentParser(
        description="Bulk compilation of laboratory instrument files."
    )
    parser.add_argument(
        "--archive",
        action="store_true",
        help="If set, search for instrument files in --input directory, and archive raw data in the directory specified by --output",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="If set, recursively search input directory.",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="If set, the files are copied to subdirectories of --output. If not set, the files are hardlinked to subdirectories.",
    )
    
    parser.add_argument(
        "--transform",
        action="store_true",
        help="If set, search for summary .json files in --output directory and transform archived raw data files as indicated in --settings file",
    )
    parser.add_argument(
        "--input",
        type=str,
        default="C:/Data/",
        help="Input directory containing instrument files.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=str,
        default="C:/Data/",
        help="Output directory for processed files.",
    )
    parser.add_argument(
        "--system",
        type=str,
        required=True,
        nargs="+",
        default=[],
        help="List of systems to process (space separated). Currently supported are: GRA PWAVE_L MS NGR SRM DSC RSC MSPOINT PROFILE RGB ROI XSCAN",
    )
    parser.add_argument(
        "--settings",
        type=str,
        help="Specify a settings .json file. If none specified, uses default settings.json in local directory.",
    )
    
    parser.add_argument(
        "--step",
        action="store_true",
        help="If set, pauses execution after each test archive or transformation."
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="If set, will overwrite existing files in archive or transform locations."
    )
    parser.add_argument(
        "--logfile",
        choices=['default','output'],
        help="If set to output, log files are written to the directory specified by --output, otherwise they are written to sodlab.exe directory."
    )

    
    args = parser.parse_args()
    
    if args.logfile and args.logfile == 'output':

        configure_logging(args.output)
    else:
        configure_logging()

    try:
        settings_path = None
        if args.settings:
            settings_path = args.settings
        else:
            logger.info(f"Using default application settings in local directory")
            settings_path = os.path.join(os.getcwd(),'settings.json')
            
            
        with open(settings_path, "r") as file:
            temp = json.load(file)
            SETTINGS = recursively_resolve_funcs(temp)
        logger.info(f"Loaded settings from {args.settings}")
    except Exception as ex:
        logger.error(ex)
        logger.error(
            "Error importing settings from specified json file. Using default settings"
        )

    if len(args.system) == 0:
        logger.warning("No instrument systems specified")
        exit(0)


    for system in args.system:
        dataLoader = DataLoader(
            path=args.input,
            analysis=system,
            output_dir=args.output,
            recursive=args.recursive,
            force= args.force,
            settings = SETTINGS,
        )
        
        keep_stepping = args.step
        
        # if copy is specified true, archive files are copied otherwise they are hardlinked.
        hardlink = not args.copy
            
        if args.archive:
            for file in dataLoader.get_instrument_files():
                dataLoader.archive(file, hardlink=hardlink)
                if keep_stepping:
                    val = input("Press Enter to step or enter any key to continue processing...")
                    if val:
                        keep_stepping = False
                        
        keep_stepping = args.step
        
        if args.transform:
            for file in dataLoader.get_summary_files():
                dataLoader.transform(file)
                if keep_stepping:
                    val = input("Press Enter to step or enter any key to continue processing...")
                    if val:
                        keep_stepping = False


if __name__ == "__main__":

    main()



    TEST = False
    if TEST:
        code = "RGB"

        dl = DataLoader(
            path=f"C:/Data/projects/ProjectD/instrument_files",
            pattern=rf".+\.{code}$",
            analysis=code,
            output_dir=f"C:/Data/projects/ProjectD",
            recursive=False,
        )

        instrument_files = dl._get_files(
            path=dl.path, pattern=dl.pattern, recursive=False
        )

        for f in instrument_files:
            dl.archive(f, hardlink=True)

        
        for f in dl.get_summary_files():
            dl.transform(f)

