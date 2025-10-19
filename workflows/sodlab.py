
import os
import shutil
import argparse
import json
import re
import logging
import logging.handlers
import io
from importlib import import_module
from pathlib import Path
from tqdm import tqdm

import pandas as pd

# NOTE: Many of these modules are imported at runtime from module methods specified in settings.json
from iodp import utils


def get_nested_dict(data, keys, default=None):
    """Safely get nested dictionary values using dot notation or list of keys."""
    if isinstance(keys, str):
        keys = keys.split('.')
    
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def configure_logging(outdir: str = None):

    outfile = "sodlab.log"

    if outdir:
        if not os.path.exists(outdir):
            raise FileNotFoundError(f"Logging directory does not exist at: {outdir}")
        outfile = os.path.normpath(os.path.join(outdir, outfile))
    else:
        # get location of where this script is running:
        path = os.path.dirname(os.path.abspath(__file__))
        outfile = os.path.normpath(os.path.join(path, outfile))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.handlers.RotatingFileHandler(
                outfile,
                mode="a",
                maxBytes=50 * (1024) ** 2,
                backupCount=5,
                encoding="utf-8",
            ),
        ],
    )

    print("")
    print(f"Logs will be written to: {outfile}")
    print("")

def get_files(path: str, pattern: str, recursive: bool) -> list:
    """Get full path references to files within a directory.

    Args:
        path (str): Input directory to search.
        pattern (str): A regex pattern to filter files by.
        recursive (bool): If True performs a recursive search of input path.

    Raises:
        FileNotFoundError: If input path does not exist.

    Returns:
        list[str]: A list of file references.
    """
    files = []
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
    

# NOTE: The configuration for this logger is set in main()
logger = logging.getLogger(__name__)



class TestSet:
    def __init__(self):
        
        # NOTE: None of these are always known at initialization. :(
        self.has_ifile = False
        self.ifile = None
        self.testfolder = None
        self.testid = None
        self.raw_files: dict = None
        self.analysis = None
        self.filekeys = None
        self.force_relative:bool = False

    def __repr__(self):
        
        file_str = "\n"
        if isinstance(self.raw_files, dict):
            for key, val in self.raw_files.items():
                file_str += f"\t\t{key}: {val}\n"
        elif isinstance(self.raw_files, list):
            for val in self.raw_files:
                file_str += f"\t\t{val}\n"
        else:
            file_str = ""
        
                
        msg = f"""
        testfolder: {self.testfolder}
        testid: {self.testid}
        ifile: {self.ifile}
        has_ifile: {self.has_ifile}
        analysis: {self.analysis}
        force_relative: {self.force_relative}
        filekeys: {self.filekeys}
        raw_files: {file_str}
        
        """
        return msg

        
    def assign_raw_files(self, how) -> None:
        """Assembles references to raw data files."""
        
        # By Instrument file
        if how == 'byfile':
            
            # NOTE: relative path will return file references relative to ifile location.
            self.raw_files = _get_raw_files_by_ifile(path=self.ifile, filekeys=self.filekeys, force_relative=self.force_relative)

        # By Folder
        if how == 'byfolder':
            self.raw_files = _get_raw_files_by_folder(path=self.testfolder)

    def contains_files(self) -> bool:
        """Checks if all the RDF are in the test folder"""
        pass
        
    def archive(self, dest, method, force) -> None:
        """Places all the raw data files in dest directory"""

        files = None
        if isinstance(self.raw_files, dict):
            files = list(self.raw_files.values())
        elif isinstance(self.raw_files, list):
            files = self.raw_files
        else:
            raise TypeError("Unable to determine type of raw file collection.")
        
        _archive(files, dest, self.analysis, self.testid, method, force)
            
  
    def get_ifile(self, pattern):
        """Indicates if the folder has one and only one instrument file.
        """
        inst_file = get_files(path = self.testfolder, pattern=pattern, recursive=False)
        
        if inst_file:
            if not len(inst_file) == 1:
                raise Exception("More than one instrument file detected in folder.")
            
            file = inst_file[0]
            
            if os.path.isfile(file) and os.path.exists(file):
                return file
    
        raise FileNotFoundError("No instrument file detected.")
    
    def get_testid_from_ifile(self):
        
        if self.has_ifile:
            _, file = os.path.split(self.ifile)
            base, _ = os.path.splitext(file)
            
            self.testid = base
            return
            
        raise Exception(f"Cannot parse testid from: {self.ifile}")
            
		
		
	
def _archive(files:list, dest:str, analysis: str, testid:str, method:str, force: bool):
    """Accepts an iterable of full filepaths(s). Places each file at destination.
    """
    dest = os.path.normpath(os.path.join(dest,analysis,testid))
    
    if not os.path.exists(dest):
        os.makedirs(dest, exist_ok=True)
        
    # stage files
    for path in files:
        oldpath = Path(path)
        newpath = os.path.join(dest,oldpath.name)
        
        if path == newpath:
            logger.warning(f"Destination path same as source path. Skipping {path}")
            continue
        
        if method  == 'hardlink':
            # Check new path is on same drive:
            if os.path.splitdrive(oldpath) != os.path.splitdrive(newpath):
                raise Exception("Cannot hard-link files on different volumes.")
            
            if os.path.exists(newpath):
                if not force:
                    logger.warning(f'File already exists at: {newpath}. Will not overwrite.')
                    continue
                else:
                    # NOTE: Unlinking when st_nlink == 1 deletes the original.
                    if os.stat(oldpath).st_nlink > 1:
                        oldpath.unlink()

            oldpath.link_to(newpath)
            logger.info(f"File hardlinked to: {newpath}")
            continue
        
        if method == 'copy':
            if os.path.exists(newpath) and not force:
                logger.warning(f'File already exists at: {newpath}. Will not overwrite.')
                continue

            
            shutil.copy2(path,newpath)
            logger.info(f"File copied to: {newpath}")
            continue

        if method == 'move':
            if os.path.exists(newpath) and not force:
                logger.warning(f'File already exists at: {newpath}. Will not overwrite.')
                continue
            
            shutil.move(path,newpath)
            logger.info(f"File moved to: {newpath}")
            continue


def _transform(test, dest:str, settings:str):

    if not os.path.exists(dest):
        raise FileNotFoundError(f"Parent transformation directory does not exist")
      
    newdir = os.path.normpath(f"{dest}/{test.analysis}/{test.testid}/transform")

    if isinstance(test.raw_files, dict):
        for key, file in test.raw_files.items():
            file_dict = get_nested_dict(settings,f"systems.{test.analysis}.files")
            if not file_dict:
                raise KeyError(f"Raw file keys not found in settings for {test.analysis}")
            
            if not key in file_dict.keys():
                logger.warning(f"Raw file key {key} not found in settings for {test.analysis}")
                continue
            
            func = _resolve_function(file_dict[key]['func'])
            kwargs = file_dict[key]['kwargs']
            depths_spec = file_dict[key].get('add_depths', None)
            
            if func is None:
                logger.info(f"No transform function specified. Skipping.")
                continue
            
            logger.info(f"{key}: Transform function: {func.__module__}.{func.__name__}, kwargs: {kwargs}")
            
            # perform transform:
            depths_added = False
            
            try:
                temp = func(file, **kwargs)
                
                # adding depths can only be to dataframes
                if isinstance(temp, pd.DataFrame):
                    if depths_spec and _convert_bool_value(depths_spec['active']):
                        depths_added = True
                        temp = utils.add_depths_to_dataframe(
                            df = temp,
                            offset_col= depths_spec['offset_col'],
                            sample_number_col = depths_spec['sample_number_col'],
                            is_textid_col = depths_spec['is_textid_col']
                        )
                        logger.info(f"Depths added to dataframe.")
            except Exception as e:
                logger.error(e)
                logger.error(f'Could not apply transformation to file: {file}. Skipping...')
                continue
                    
            # move file to new dir
            _, filename = os.path.split(file)
            base, _ = os.path.splitext(filename)
            
            # Special handling depending on filetype:
            # BytesIO stream examples are NGR .zip files and SHIL .tiff images.
            os.makedirs(newdir, exist_ok=True)
            
            if isinstance(temp, io.BytesIO):
                dest_path = os.path.join(newdir, filename)
                with open(dest_path, 'wb') as f:
                    f.write(temp.read())
            elif isinstance(temp, pd.DataFrame):
                if key == 'instrument_file':
                    dest_path = os.path.join(newdir, f"instrument_file_{base}.csv")
                else:
                    dest_path = os.path.join(newdir, f"{base}.csv")
                    
                temp.to_csv(dest_path, index=False)
            else:
                logger.error(f"Unspecified output file type for temp file with datatype {type(temp)}. Skipping...")
                continue
            
            logger.info(f"File written to: {dest_path}")
    
        
def is_analysis_folder(path: str, pattern:str):
    """Checks if a folder is part of an analysis by looking for a matching file within the folder.

    Args:
        path (str): Path to folder
        pattern (str): A regex pattern to match files on.
    """
   
    if not os.path.isdir(path):
       raise Exception(f"Path is not a folder: {path}")
   
   # uses a regex string to find a file within the folder.
    try:
        reg = re.compile(pattern)
        for file in os.listdir(path):
            if reg.match(file):
                return True
        return False
    except Exception as e:
        logger.error(f"{e}")
        return False
            
def _get_raw_files_by_ifile(path:str, filekeys, force_relative) -> list:
    """User specifies a ifile. The ifile handle, and all files/folders listed within are returned."""
    files = _verify_ifile(path, filekeys, force_relative)
    
    return files
	
def _get_raw_files_by_folder(path:str) -> list:
    """User specifies a path. All files/folders within are returned."""
    
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} does not exist")
    
    files = [os.path.normpath(os.path.join(path, file)) for file in os.listdir(path)]
    return files
    
    
 
def _verify_ifile(ifile:str, filekeys, force_relative=False) -> list:
    """Checks the raw data file references within an instrument file. Verifies their existence. Relative filepaths are relative to the same folder containing the provided instrument file.

    Args:
        file (str): The full filepath to the instrumet file (ifile).
        filekeys (list): An iterable of file keys listed in the <FILE></FILE> section of an instrument file.

    Raises:
        KeyError: Raw data file key is not present in instrument file
        Exception: Paths in instrument file are not absolute paths when specified to be so.
        FileNotFoundError: Raw data file does not exist at specified absolute path.
        FileNotFoundError: Alternatively, raw data file does not exist in "file" folder.

    Returns:
        list: Returns a list of tuples. Each tuple is a file key name and a full filepath.
    """
    files = dict()
    
    contents: dict = utils.read_instrument_file(ifile, as_dataframe=False)
    
    for key in filekeys:
        if not key in contents:
            # NOTE: 10/17/2025 instrument file keys do not exist in filekeys yet. This behavior is to be altered.
            if key == 'instrument_file':
                continue
            else:
                raise KeyError(f"File key: {key} not found in instrument file")
        
        filepath: str = contents[key]
        
        # Determine if filepath is an absolute path, relative path, or not a path
        # Check raw file is truly an abs path.
        
    
        localdir = os.path.dirname(ifile)
        
        if force_relative:
          
            _, base = os.path.split(filepath)
            check_path = os.path.join(localdir, base)
            if not os.path.exists(check_path):
                raise FileNotFoundError(f'Raw data file does not exist at path: {filepath}')
            
            files[key] = os.path.normpath(check_path)
            continue
            
        
        if os.path.isabs(filepath):
            if not os.path.exists(filepath):
                raise FileNotFoundError(f'Raw data file does not exist at path: {filepath}')
            
        
            files[key] = os.path.normpath(filepath)
            continue
        
        else:
            # NOTE: If filepath is relative, it must exist in same directory as the instrument file.
            created_filepath = os.path.normpath(os.path.join(localdir, filepath))
            
            assert os.path.isabs(created_filepath)
            
            if not os.path.exists(filepath):
                raise FileNotFoundError(f'Raw data file does not exist at path: {filepath}')
            
            files[key] = os.path.normpath(created_filepath)
            continue
   
    # add in the instrument file reference too:
    if 'instrument_file' not in contents:
        files["instrument_file"] = os.path.normpath(ifile)
    
    return files

    
class DataLoader:
    """Class to handle archiving and transforming raw data files from SOD track systems controlled by IMS."""

    def __init__(
        self,
        source: str,
        analysis: str,
        output_dir: str,
        recursive: bool = False,
        force_overwrite: bool = False,
        settings: str = None,
    ):

        self.path = source
        self.recursive = recursive
        self.analysis = analysis
        self.force_overwrite = force_overwrite
        self.settings = settings
        
        self.tests = []

        self.graph = self.settings["systems"][self.analysis]

        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            self.output_dir = output_dir
        except Exception as e:
            logger.error(f"Failed to create output directory '{output_dir}': {e}")
            raise
        
        
        
    def collect_tests(self, how, force_relative_paths):
        # NOTE: In both cases below, an ifile is present somewhere. So these mechanisms only work for tracks.
        
        pattern = get_nested_dict(self.graph,'files.instrument_file.pattern')
        
        logger.info(f"{self.analysis}: Searching for tests in: {self.path}. (recursive: {self.recursive})")
        
        # TODO: byfolder approach is currently unused/untested. V.P. 10/17/2025
        if how=='byfolder':
            recurse = False
            for folder in os.listdir(self.path):
                
                fullpath =  os.path.normpath(os.path.join(self.path,folder))
                if not os.path.isdir(fullpath): continue
                if not is_analysis_folder(fullpath, pattern): continue
                
                # Create a TestSet. Populate fields
                try:
                    test = TestSet(fullpath)
                    test.analysis = self.analysis
                    test.assign_raw_files(how="byfolder")
                    test.ifile = test.get_ifile(pattern=pattern)
                    
                    if test.ifile: test.has_ifile = True
            
                    test.get_testid_from_ifile()
                    self.tests.append(test)
                    
                except Exception as e:
                    logger.error(e)
            
            
        if how=='byfile':
            files = get_files(self.path,pattern=pattern,recursive=self.recursive)
            for file in files:    
                try:
                    # NOTE: test folder path is not determined at this time.
                    
                    test = TestSet()
                    test.filekeys = self.graph['files'].keys()
                    test.analysis = self.analysis
                    test.has_ifile = True
                    test.ifile = file
                    test.force_relative = force_relative_paths
                    test.assign_raw_files(how='byfile')
                    test.get_testid_from_ifile()
                    self.tests.append(test)
                    
                except Exception as e:
                    logger.error(e)
        
        logger.info(f"{self.analysis}: Found {len(self.tests)} tests in input directory. (recursive: {self.recursive})")
    
    def archive(self, method, **kwargs):
        
        step = False
        if "step" in kwargs:
            step = kwargs['step']
            
        test: TestSet
        for test in self.tests:
                    
            print("")
            GREEN = "\033[92m"
            RESET = "\033[0m"
            logger.info(f"{GREEN}Creating archive for {test.testid}{RESET}")
            
            test.archive(dest=self.output_dir, method=method, force=self.force_overwrite)
            
            if step:
                    val = input(
                        "Press Enter to step or enter any key to continue processing..."
                    )
                    if val:
                        step = False
                        
            
    def transform(self, **kwargs):
        
        step = False
        if "step" in kwargs:
            step = kwargs['step']
            
        test: TestSet
        for test in self.tests:
            print("")
            GREEN = "\033[92m"
            RESET = "\033[0m"
            logger.info(f"{GREEN}Applying transforms for {test.testid}{RESET}")
            
            _transform(test, dest=self.output_dir, settings=self.settings)
            
            if step:
                    val = input(
                        "Press Enter to step or enter any key to continue processing..."
                    )
                    if val:
                        step = False
                          

def _resolve_function(func_path: str):
    """Convert 'module.func' string into a function reference."""
    module_name, func_name = func_path.rsplit(".", 1)
    module = import_module(module_name)
    return getattr(module, func_name)


def _recursively_resolve_funcs(obj):
    """Recursively resolve any 'func' keys that contain a string path."""
    if isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            if k == "func" and isinstance(v, str):
                new_dict[k] = _resolve_function(v)
            else:
                new_dict[k] = _recursively_resolve_funcs(v)
        return new_dict
    elif isinstance(obj, list):
        return [_recursively_resolve_funcs(item) for item in obj]
    else:
        return _convert_bool_value(obj)


def _convert_bool_value(value):
    """Convert string booleans to actual bools."""
    if isinstance(value, str):
        lower = value.strip().lower()
        if lower == "true":
            return True
        elif lower == "false":
            return False
        else:
            raise ValueError('Value is not a parseable boolean.')
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
        "--transform",
        action="store_true",
        help="If set, search for summary .json files in --output directory and transform archived raw data files as indicated in --settings file",
    )
    
    parser.add_argument(
        "--compile",
        action="store_true",
        help="If set, navigates through the directory specified by --output and compiles transformed files into singular reports"
    )
    
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="If set, recursively search input directory.",
    )
    # parser.add_argument(
    #     "--copy",
    #     action="store_true",
    #     help="If set, the files are copied to subdirectories of --output. If not set, the files are hardlinked to subdirectories.",
    # )
    
    parser.add_argument(
        "--input",
        type=str,
        default="C:/Data/",
        help="Input directory to be searched. Will be searched recursively if --recursive flag is active.",
    )
    
    parser.add_argument(
        "--force_relative_paths",
        action="store_false",
        help="Forces interpretation of filepaths in instrument file as paths relative to the folder storing the instrument file.",
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
        help="If set, pauses execution after each test archive or transformation.",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="If set, will overwrite existing files in archive or transform locations.",
    )
    parser.add_argument(
        "--logfile",
        choices=["default", "output"],
        help="If set to output, log files are written to the directory specified by --output, otherwise they are written to sodlab.exe directory.",
    )


    args = parser.parse_args()
    
    try:
        if args.compile and (args.archive or args.transform):
            parser.error("--compile cannot be used with --archive or --transform")
    except:
        exit(0)

    if args.logfile and args.logfile == "output":

        configure_logging(args.output)
    else:
        configure_logging()

    try:
        # NOTE: Default settings should be from where the app is running
        settings_path = None
        if args.settings:
            settings_path = args.settings
        else:
            logger.info(f"Using default application settings in local directory")
            settings_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "settings.json"
            )
        with open(settings_path, "r") as file:
            settings = json.load(file)
            
        logger.info(f"Loaded settings from {settings_path}")
    except Exception as ex:
        logger.error(ex)
        logger.error(
            "Error importing settings from specified json file. Using default settings"
        )

    if len(args.system) == 0:
        logger.warning("No instrument systems specified")
        exit(0)

    
    
    for system in args.system:
        
    
        if args.archive or args.transform:
            data_loader = DataLoader(
                source=args.input,
                analysis=system,
                output_dir=args.output,
                recursive=args.recursive,
                force_overwrite=args.force,
                settings=settings,
            )
        
            
            data_loader.collect_tests(how='byfile', force_relative_paths=args.force_relative_paths)
                    
            if args.archive:
                data_loader.archive(method='copy', step=args.step)
                
            if args.transform:
                data_loader.transform(step=args.step)




        if args.compile:
            
            try:
                    
                if not os.path.exists(args.output):
                    os.makedirs(args.output)
                    
                files = []
                pattern = '^instrument_file_.+\\.csv$'
            
                files = get_files(args.input, pattern=pattern, recursive=args.recursive)
                
                if len(files) == 0:
                    logger.warning(f"{system}: No files found in input directory (recursive = {args.recursive})")
                    continue
    
                df = pd.DataFrame()
                
                for file in tqdm(files, desc="Compiling csvs", unit="file"):
                    try:
                        df_ = pd.read_csv(file)
                        
                        # sort = False allows dataframes with different columns to be concatenated
                        # missing values are filled with NaN.
                        df = pd.concat([df,df_],axis=0, ignore_index=True, sort=False)
                        
                    except Exception as e:
                        logger.error(f"Error adding {file} to compilation ")
                        continue
                    
                df.reset_index(drop=True)
                
                comp_filepath = os.path.normpath(os.path.join(args.output, f"{system}_compilation.csv"))
                
                df.to_csv(comp_filepath, index=False)
                
                logger.info(f"Writing compilation file to {comp_filepath}")
                
            except Exception as e:
                logger.error(e)


                
            
        continue
    
            
            


if __name__ == "__main__":

    main()
    
    # Below is only for immediate testing.
    TEST = False
    if TEST:
        analysis = 'GRA'
        source = "D:/archive/hd_files/data_analysis/50_laboratory_notebooks/SOD-Laboratory/PhysicalProperties/data/input"
        #source = 'C:\\Users\\vpercuoco\\Desktop\\output\GRA'
        recurse = True
        dest = 'C:\\Users\\vpercuoco\\Desktop\\output'
        force_overwrite = True
        force_relative = True
        step = False
        
        settings = None
        with open("D:/archive/hd_files/data_analysis/50_laboratory_notebooks/SOD-Laboratory/workflows/settings.json", "r") as file:
            settings = json.load(file)
        
        
        dl = DataLoader(
            source=source,
            analysis=analysis,
            output_dir=dest,
            recursive=recurse,
            force_overwrite=force_overwrite,
            settings=settings)
        
        
        dl.collect_tests(how='byfile', force_relative_paths=force_relative)
        
        dl.archive(method='copy', step=step)
        
        dl.transform(step=step)
    
    
