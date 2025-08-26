import sys
import os
from importlib import reload, import_module

from huggingface_hub import SummarizationOutput
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from functools import partial

import test

from iodp import utils, ngr, pwavel, srm, shmsl, ms, rgb

import re
import zipfile
import logging
import io

from pathlib import Path
import argparse
import json
import shutil

# Configure logger
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s [%(levelname)s] %(message)s",
#     handlers=[
#         logging.StreamHandler()
#     ]
# )
# logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bulk_compilation.log", mode='a')
    ]
)

logger = logging.getLogger(__name__)



SETTINGS = {
    "PWAVE_L": {
        "analysis": "PWAVE_L",
        "instrument_file": {
            "func": utils.read_instrument_file,
            "kwargs": {"as_dataframe": True},
            "add_depths" : {
                "active": False,
                "offset_col" : 'offset',
                "sample_number_col" : "text_id",
                "is_textid_col": True
            }
        },
        "files": {
            "velocity_wfm": {
                "func": pwavel.read_pwavel_csv,
                "kwargs": {}
            },
            "config": {
                "func": utils.read_instrument_ini,
                "kwargs": {"as_dataframe": True}
            },
        }
    },
    "MS": {
        "analysis": "MS",
        "instrument_file": {
            "func": utils.read_instrument_file,
            "kwargs": {"as_dataframe": True},
            "add_depths" : {
                "active": False,
                "offset_col" : 'offset',
                "sample_number_col" : "text_id",
                "is_textid_col": True
            }
            },
        "files": {
            "aux_file": {
                "func": ms.read_ms_csv,
                "kwargs": {},
            "add_depths" : {
                "active": False,
                "offset_col" : 'offset(cm)',
                "sample_number_col" : "text_id",
                "is_textid_col": True
            }
            },
            "config": {
                "func": utils.read_instrument_ini,
                "kwargs": {"as_dataframe": True}
            }
        }
    },
    "GRA": {
        "analysis": "GRA",
        "instrument_file": {
            "func": utils.read_instrument_file,
            "kwargs": {"as_dataframe": True},
            "add_depths" : {
                "active": False,
                "offset_col" : 'offset',
                "sample_number_col" : "text_id",
                "is_textid_col": True
            }
            },
        "files": {
            "config": {
                "func": utils.read_instrument_ini,
                "kwargs": {"as_dataframe": True}
            }
        }
    },
    "RSC": {
        "analysis": "RSC",
        "instrument_file": {
            "func": utils.read_instrument_file,
            "kwargs": {"as_dataframe": True},
            "add_depths" : {
                "active": False,
                "offset_col" : 'offset',
                "sample_number_col" : "text_id",
                "is_textid_col": True
            }
            },
        "files": {
            "rsc_norm": {
                "func": pd.read_csv,
                "kwargs": {}
            },
            "rsc_raw": {
                "func": pd.read_csv,
                "kwargs": {}
            },
            "config": {
                "func": utils.read_instrument_ini,
                "kwargs": {"as_dataframe": True}
            }
        }
    },
    "PROFILE": {
        "analysis": "PROFILE",
        "instrument_file": {
            "func": utils.read_instrument_file,
            "kwargs": {"as_dataframe": True}
            
            },
        "files": {
            "profile": {
                "func": pd.read_csv,
                "kwargs": {},
                "add_depths" : {
                     "active": False,
                    "offset_col" : 'benchmark offset(cm)',
                    "sample_number_col" : "text_id",
                    "is_textid_col": True
            }
            },
            "config": {
                "func": utils.read_instrument_ini,
                "kwargs": {"as_dataframe": True}
            }
        }
    },
    "MSPOINT": {
        "analysis": "MSPOINT",
        "instrument_file": {
            "func": utils.read_instrument_file,
            "kwargs": {"as_dataframe": True},
            "add_depths" : {
                "active": False,
                "offset_col" : 'offset',
                "sample_number_col" : "text_id",
                "is_textid_col": True
            }
            },
        "files": {
            "aux_file": {
                "func": pd.read_csv,
                "kwargs": {}
            },
            "config": {
                "func": utils.read_instrument_ini,
                "kwargs": {"as_dataframe": True}
            }
        }
    },
    "RGB": {
        "analysis": "RGB",
        "instrument_file": {
            "func": utils.read_instrument_file,
            "kwargs": {"as_dataframe": True},
            "add_depths" : {
                "active": False,
                "offset_col" : 'offset',
                "sample_number_col" : "text_id",
                "is_textid_col": True
            }
            },
        "files": {
            "config": {
                "func": utils.read_instrument_ini,
                "kwargs": {"as_dataframe": True}
            }
        },
        "rgb_high_res" : {
            "func": rgb.read_rgb_high_res_dat,
            "kwargs": {"as_dataframe": True}
        }
    },
    "ROI": {
        "analysis": "LSIMG",
        "files": {
            "original_image": {
                "func": utils.copy_file,
                "kwargs": {}
            },
            "consumer_image": {
                "func": utils.copy_file,
                "kwargs": {}
            },
            "cropped_image": {
                "func": utils.copy_file,
                "kwargs": {}
            },
            "config": {
                "func": utils.read_instrument_ini,
                "kwargs": {"as_dataframe": True}
            }
        }
    },
    "NGR": {
        "analysis": "NGR",
        "instrument_file": {
            "func": utils.read_instrument_file,
            "kwargs": {"as_dataframe": True},
            "add_depths" : {
                "active": False,
                "offset_col" : 'offset',
                "sample_number_col" : "text_id",
                "is_textid_col": True
            }
            },
        "files": {
            "archive": {
                "func": ngr.read_zip_file,
                "kwargs": {}
            },
            "configuration": {
                "func": utils.read_instrument_ini,
                "kwargs": {"as_dataframe": True}
            },
            "summary": {
                "func": pd.read_csv,
                "kwargs": {},
                "add_depths" : {
                    "active": False,
                    "offset_col": "Offset",
                    "sample_number_col": "Text_ID",
                    "is_textid_col": True
                }
            }
        }
    },
    "SRM": {
        "analysis": "SRM",
        "instrument_file": {
            "func": utils.read_instrument_file,
            "kwargs": {"as_dataframe": True},
            "add_depths" : {
                "active": True,
                "offset_col" : 'offset',
                "sample_number_col" : "text_id",
                "is_textid_col": True
            }
            },
        "files": {
            "file_srm_section_bkgnd": {
                "func": srm.read_srm_csv,
                "kwargs": {}
            },
            "file_raw": {
                "func": srm.read_srm_csv,
                "kwargs": {}
            },
            "file_srm_sequence": {
                "func": utils.read_instrument_ini,
                "kwargs": {"as_dataframe": True}
            },
            "file_configuration": {
                "func": utils.read_instrument_ini,
                "kwargs": {"as_dataframe": True}
            }
        }
    },
    "DSC": {
        "analysis": "DSC",
        "instrument_file": {
            "func": utils.read_instrument_file,
            "kwargs": {"as_dataframe": True},
            "add_depths" : {
                "active": False,
                "offset_col" : 'offset',
                "sample_number_col" : "text_id",
                "is_textid_col": True
            }
            },
        "files": {
            "file_srm_discrete_bkgnd": {
                "func": srm.read_srm_csv,
                "kwargs": {}
            },
            "file_raw": {
                "func": srm.read_srm_csv,
                "kwargs": {}
            },
            "file_srm_sequence": {
                "func": utils.read_instrument_ini,
                "kwargs": {"as_dataframe": True}
            },
            "file_configuration": {
                "func": utils.read_instrument_ini,
                "kwargs": {"as_dataframe": True}
            }
        }
    },
    "XSCAN": {
        "analysis": "XSCAN",
        "instrument_file": {
            "func": utils.read_instrument_file,
            "kwargs": {"drop_fields":['calib_dark_raw', 'calib_white_raw'], "as_dataframe": True}
            },
        "files": {
            "raw_image": {
                "func": utils.copy_file,
                "kwargs": {}
            },
            "processed_crop_image": {
                "func": utils.copy_file,
                "kwargs": {}
            },
            "processed_ruler_image": {
                "func": utils.copy_file,
                "kwargs": {}
            },
            "config": {
                "func": utils.read_instrument_ini,
                "kwargs": {"as_dataframe": True}
            }
        }
    }
}

class DataLoader:
    def __init__(self, path:str, pattern:str, analysis:str, output_dir:str, recursive:bool = False, ):
        
        self.pattern = pattern
        self.path = path
        self.recursive = recursive
        self.analysis = analysis
        
        # Check if path and output_dir are on the same drive
        # Hard-linked files can only exist on same volume.
        # path_drive = os.path.splitdrive(os.path.abspath(path))[0]
        # output_drive = os.path.splitdrive(os.path.abspath(output_dir))[0]
        # if path_drive and output_drive and path_drive.lower() != output_drive.lower():
        #     raise ValueError(f"Source path '{path}' and output directory '{output_dir}' are not on the same drive.")

        self.graph = SETTINGS[self.analysis]
        
        # self.inst_files = self._get_files(
        #     self.path,
        #     self.pattern,
        #     self.recursive
        # )
           
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            self.output_dir = output_dir
        except Exception as e:
            logger.error(f"Failed to create output directory '{output_dir}': {e}")
            raise
            
       
    
    def _get_files(self, path:str, pattern:str, recursive:bool):
        
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
    
    
    def _archive_test_files(self, instrument_file, hardlink: True):
        
        summary = {}
        summary['raw_files'] = {}
        summary['analysis'] = self.analysis
        summary['instrument_file'] = instrument_file
        
        
        print("")
        GREEN = '\033[92m'
        RESET = '\033[0m'
        logger.info(f"{GREEN}Organizing raw data files for file: {instrument_file}{RESET}")
        
        if not os.path.isfile(instrument_file):
            logger.error(f"File does not exist: {instrument_file}")
            raise
        
        inst_filename = os.path.basename(instrument_file)
        
        # The testid is the root name of the file. It follows a format of TEXTID/SAMPLENAME - DATETIME
        testid, _ = os.path.splitext(inst_filename)
        
        summary['testid'] = testid
       
        contents: dict = utils.read_instrument_file(instrument_file, as_dataframe=False)
        
        raw_files = []
        
        # all file references are stored in the <FILE></FILE> section
        for file_name_key in self.graph['files'].keys():
            raw_files.append((file_name_key,contents[file_name_key]))
            
        # location where RDF will be stored for TEST
        analysis_path = os.path.normpath(os.path.join(self.output_dir, self.analysis))
        test_path = os.path.normpath(os.path.join(self.output_dir, self.analysis, testid))
        test_raw_path = os.path.normpath(os.path.join(test_path, "raw"))
        
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
                summary['raw_files'][file_name_key] = {}
                
                # verify raw file exists at source:
                if not os.path.exists(file):
                    logger.error(f"{file_name_key}: Raw data file does not exist at source: {file}")
                    continue
                
                filename  = os.path.basename(file)
                new_path = os.path.join(test_raw_path, filename)
                
                if os.path.exists(new_path):
                    os.unlink(new_path)
                    
                if hardlink:
                    os.link(file, new_path)      
                    logger.info(f"{file_name_key}: File hard-linked to: {new_path}")          
                    
                    summary['raw_files'][file_name_key]['hardlinked'] = str(True)
                else:
                    shutil.copy2(file, new_path)
                    logger.info(f"{file_name_key}: File copied to: {new_path}")
                    
                    summary['raw_files'][file_name_key]['hardlinked'] = str(False)
                
                
                summary['raw_files'][file_name_key]['original_path'] = file
                summary['raw_files'][file_name_key]['basename'] = filename
                #summary['raw_files'][file_name_key]['new_path'] = new_path
                summary['raw_files'][file_name_key]['relative_path'] = os.path.relpath(new_path,analysis_path)

        except Exception as e:
            logger.error(e)
            logger.error(f"Error creating file archive for test: {testid}")
            raise
        
        # output the summary
        summary_path = os.path.join(test_path, f"summary_{self.analysis.lower()}_{testid}.json")
        with open(summary_path, "w") as f:
            summary_ordered = self._sort_summary(summary)
            json.dump(summary_ordered, f, indent=4)
            logger.info(f"Summary written to: {summary_path}")
        
 
    def _transform_archived_test_files(self, summary_file):
        """Uses the summary file to reference files. Assumes the files exist in a local directory. The summary file is a .json file.
        """
        
        # NOTE: The summary file is nested in a test folder.
        
        summary = None
        
        if not os.path.isfile(summary_file):
            raise FileNotFoundError(f"Test summary file does not exist at: {summary_file}")
    
        print("")
        GREEN = '\033[92m'
        RESET = '\033[0m'
        logger.info(f"{GREEN}Applying transformations for test summary file: {summary_file}{RESET}")
        
        test_dir = os.path.dirname(summary_file)
        test_parent_dir = os.path.dirname(test_dir)

        with open(summary_file, "r") as f:
            summary = json.load(f)
            
        summary['transformed_files'] = {}
    
        raw_data_files = summary['raw_files']
        
        for file_name_key, rdf in raw_data_files.items():
            
            # NOTE: relative path starts in a folder named by testid
            src = rdf.get('relative_path',None)

            if src is None:
                logger.info(f"instrument file: {src}, {file_name_key}: Has no file reference.")
                continue
        
            src = os.path.join(test_parent_dir, src)
            
            summary['transformed_files'][file_name_key] = {}
            summary['transformed_files'][file_name_key]['original_path'] = src
            
            
            if file_name_key == 'instrument_file':
                transform_func = SETTINGS[self.analysis]['instrument_file']['func']
                kwargs = SETTINGS[self.analysis]['instrument_file']['kwargs']
                depths_spec = SETTINGS[self.analysis]['instrument_file'].get("add_depths",None)
            else: 
                transform_func = SETTINGS[self.analysis]['files'][file_name_key]['func']
                kwargs = SETTINGS[self.analysis]['files'][file_name_key]['kwargs']
                depths_spec = SETTINGS[self.analysis]['files'][file_name_key].get("add_depths",None)
            
            # RDF will exist in the test directory
            if not os.path.isfile(src):
                raise FileNotFoundError(f"{file_name_key}: File does not exist at: {src}")
            
            logger.info(f"{file_name_key}: Source file location: {src}")
            
            if transform_func is None:
                logger.info(f"No transform function specified. Skipping.")
                continue
            
            logger.info(f"{file_name_key}: Transform function: {transform_func.__module__}.{transform_func.__name__}, kwargs: {kwargs}")
            
            depths_added = False
            try:
                # the variable here may be a range of different data types.
                temp = transform_func(src, **kwargs)
                
                if isinstance(temp, pd.DataFrame):
                    if depths_spec and depths_spec.get('active', None):
                            depths_added = True
                            temp = utils.add_depths_to_dataframe(
                                df=temp,
                                offset_col=depths_spec.get('offset_col', None),
                                sample_number_col=depths_spec.get('sample_number_col', None),
                                is_textid_col=depths_spec.get('is_textid_col', None)    
                            )
          
            except Exception as e:
                logger.error(e)
                logger.error(f"Could not apply transformation to file: {src}. Skipping...")
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
                if file_name_key == 'instrument_file':
                    destination_path = os.path.normpath(
                        os.path.join(test_dir, "transform", f"instrument_file_{raw_filename_root}") + ".csv"
                        )
                else:
                    destination_path = os.path.normpath(
                        os.path.join(test_dir, "transform", raw_filename_root) + ".csv"
                        )
                os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                
                temp.to_csv(destination_path,index=False)
                
            else:
                logger.error(f"Unspecified output file type for temp file with datatype {type(temp)}. Skipping...")
                continue
            

            summary['transformed_files'][file_name_key]['basename'] = os.path.split(destination_path)[-1]
            summary['transformed_files'][file_name_key]['relative_path'] = os.path.relpath(destination_path, test_parent_dir )
            summary['transformed_files'][file_name_key]['transform'] = f"{transform_func.__module__}.{transform_func.__name__}"
            summary['transformed_files'][file_name_key]['kwargs'] = kwargs
            summary['transformed_files'][file_name_key]['add_depths'] = depths_added
            
            logger.info(f"{file_name_key}: Transformed file saved to: {destination_path}")
            
        with open(summary_file, "w") as f:
            summary_ordered = self._sort_summary(summary)
            json.dump(summary_ordered, f, indent=4)
            logger.info(f"Summary written to: {summary_file}")


    def _sort_summary(self, dict:dict):
        """Sorts the summary dictionary in a pre-defined key ordering.

        Args:
            dict (dict): _description_

        Returns:
            _type_: _description_
        """
        
        key_order = ['analysis', 'testid', 'instrument_file', 'raw_files', 'transformed_files']
        
        sorted_dict = {k: dict[k] for k in key_order if k in dict}
        
        return sorted_dict
        
        
        
        



def read_instrument_file(path: str, extension: str, destination: str) -> None:
    """Reads a LabView instrument file (.NGR, .MSPOINT, .GRA, etc), transforms its file references into .csv file format, saves them to a single test folder.

    Args:
        path (str): A folder in which to search for instrument files.
        extension (str): The extension of the LabView instrument file (.NGR, .MSPOINT, .GRA, .roi, etc)).
        destination (str): A folder path in which organized test folders will be placed.
    """
    if path is None:
        path = "C:/data/in"
    
    logger.info(f"Searching path: {path} for instrument files with extension: {extension}")
    
    pat = rf"^(?P<root>.+).{extension}$"

    files = os.listdir(path)


    # gets the matching files and their filename roots
    matched_files = [(f, re.match(pat, f).groupdict()) for f in files if re.match(pat, f)]
    
    cnt = len(matched_files)
    logger.info(f"Found {cnt} file(s).")
    if not cnt > 0:
        return
    
    
    for file, groups in matched_files:
        print("")
        GREEN = '\033[92m'
        RESET = '\033[0m'
        logger.info(f"{GREEN}Processing file: {file}{RESET}")
        
        test_folder = groups['root']
        logger.info(f"Organizing files for test within folder named: {test_folder}")
        
        # Try to read the instrument file
        instrument_file = None
        instrument_file_tabular = None
        try:
            instrument_file_path = os.path.join(path,file)
            instrument_file = utils.read_instrument_file(instrument_file_path)
            
            kwargs_spec = SETTINGS[extension]['instrument_file'].get("kwargs",None)
            instrument_file_tabular = utils.read_instrument_file(instrument_file_path, as_dataframe=True, **kwargs_spec)
            
            # Add depths is specified
            specs = SETTINGS[extension].get("instrument_file", None)
            depths_spec = None
            if specs:
                depths_spec = SETTINGS[extension]['instrument_file'].get("add_depths",None)
            if depths_spec:
                if depths_spec['active']:            
                    instrument_file_tabular = utils.add_depths_to_dataframe(
                        df=instrument_file_tabular,
                        offset_col=depths_spec['offset_col'],
                        sample_number_col=depths_spec['sample_number_col'],
                        is_textid_col=depths_spec['is_textid_col']    
                    )
                    
            
        except Exception as ex:
            logger.error(ex)
            logger.error(f"Error reading instrument file: {file}")
        
    
        
        # Transform the summary file: 
        analysis = SETTINGS[extension]['analysis']
        raw_filename = os.path.split(instrument_file_path)[-1]
        raw_filename_root, ext = os.path.splitext(raw_filename)
        destination_path = os.path.normpath(
            os.path.join(destination, analysis, test_folder, f"{analysis}_instrument_file_{raw_filename_root}") + ".csv"
            )
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        instrument_file_tabular.to_csv(destination_path,index=False)
        logger.info(f'File written to: {destination_path}')
        
        # Get the list of file keys within files with supplied extension
        file_ref_keys = list(SETTINGS[extension]['files'].keys())
        
        
        # Iterate through keys. Apply specific file transform to each file. Save transformed file copies to new location
        for file_key in file_ref_keys:

            full_file_path = instrument_file[file_key]
            
            if full_file_path is None:
                logger.info(f"instrument file: {file}, {file_key}: Has no file reference.")
                continue
            
            logger.info(f"Processing {file_key}: {full_file_path}")
            
            
            transform_fn = SETTINGS[extension]['files'][file_key]['func']
            trans_kwargs = SETTINGS[extension]['files'][file_key]['kwargs']
            
            temp = None
            if transform_fn is None:
                logger.info(f"Will simply copy file to new location.")
            else:
                logger.info(f"Will transform file using function: {transform_fn} with kwargs: {trans_kwargs}")
                
                try:
                    temp = transform_fn(full_file_path, **trans_kwargs)
                    
                    if isinstance(temp, pd.DataFrame):
                        depths_spec = SETTINGS[extension]['files'][file_key].get("add_depths",None)
                        if depths_spec:
                            if depths_spec['active']:
                                temp = utils.add_depths_to_dataframe(
                                    df=temp,
                                    offset_col=depths_spec['offset_col'],
                                    sample_number_col=depths_spec['sample_number_col'],
                                    is_textid_col=depths_spec['is_textid_col']    
                                )
        
                    
                except Exception as e:
                    logger.error(e)
                    logger.error(f"Could not apply transformation to file: {full_file_path}. Skipping...")
                    continue
            
           
            raw_filename = os.path.split(full_file_path)[-1]
            raw_filename_root, ext = os.path.splitext(raw_filename)
            
            # Currently BytesIO are for zip files from the NGR (.zip) and SHIL images (.tiff, .jpg, etc)
            if isinstance(temp, io.BytesIO):
                destination_path = os.path.normpath(
                    os.path.join(destination, analysis, test_folder, raw_filename_root) + ext
                    )
                os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                with open(destination_path, "wb") as f:
                    f.write(temp.read())       

            elif isinstance(temp, pd.DataFrame):
                destination_path = os.path.normpath(
                    os.path.join(destination, analysis, test_folder, raw_filename_root) + ".csv"
                    )
                os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                
                temp.to_csv(destination_path,index=False)
                
            else:
                logger.error(f"Unspecified output file type for temp file with datatype {type(temp)}. Skipping...")
                continue
            
            
            logger.info(f"Saved transformed file to: {destination_path}")
            
            
        
            
    print("\n\n")    
    return


#endregion

def make_compilation(path: str, system: str):
    
    # systems = ['GRA','PWAVE-L', 'MS', 'NGR', 'RSC', 'MSPOINT', 'RGB', 'SRM', 'DSC']

    
    try:
       
        search_path = os.path.normpath(os.path.join(path,system))
        
        logger.info(f"Attempting to compile instrument file csvs into a single file, recursively searching: {search_path}")

        # set the regex pattern to filter out files
        
        pat = rf'.+{re.escape(system)}_instrument_file_.+$'
    
        os.listdir(search_path)
        all_files = []
        for root, dirs, files in os.walk(path):
            for file in files:
                all_files.append(os.path.normpath(os.path.join(root, file)))

        files = [f for f in all_files if re.match(pat,f)]

        logger.info(f"Found {len(files)} matching file(s).")
        
        df = None
        
        if len(files) > 0:
            # Combine all CSV files in the 'files' list into a single DataFrame
            # Values are sorted by sample hierarchy.
            df_combined = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)

            df = df_combined.sort_values(by=['expedition','site','hole', 'core', 'section', 'sect_half', 'depth_csfa_m'])

        # by hole
        df[['expedition','site','hole']] = df[['expedition','site','hole']].astype(str)
        
        unique_combinations = df[['expedition','site','hole']].drop_duplicates()
        logger.info(f"The unique hole combinations are:\n{unique_combinations}")
        
        logger.info("Attempting to split dataframe by hole.")
        for idx, row in unique_combinations.iterrows():
            try:
                
                exp = unique_combinations.loc[idx, 'expedition']
                site = unique_combinations.loc[idx, 'site']
                hole = unique_combinations.loc[idx, 'hole']
                df_ = df.query(f"expedition == '{exp}' and site == '{site}' and hole == '{hole}'")
                
                '''
                # Ensure exp and site are string without decimals if they are float
                if isinstance(exp, float):
                    exp = str(int(exp))
                if isinstance(site, float):
                    site = str(int(site))
                '''  
                outpath = os.path.normpath(search_path + f"/{system}_compilation_{str(exp)}-{str(site)}{str(hole)}.csv")
                
                logger.info(f"Hole csv saved to: {outpath}")
                df_.to_csv(outpath, index=False)
            except Exception as ex:
                logger.error(ex)
                logger.error('Error making hole compilation file')
            
     
        outpath = os.path.normpath(search_path + f"/{system}_compilation.csv")
    
        
        df.to_csv(outpath, index=False)
        logger.info(f"Compilation csv saved to: {outpath}")
    except Exception as ex:
        logger.error(ex)
        logger.error("Error making compilation file from raw data.")
        

def resolve_function(func_path: str):
    """Convert 'module.func' string into a function reference."""
    module_name, func_name = func_path.rsplit('.', 1)
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
    # systems = ['GRA','PWAVE_L', 'MS', 'NGR', 'PROFILE', 'RSC', 'MSPOINT', 'RGB', 'SRM', 'DSC']
    
    # for system in systems:
    #    read_instrument_file("C:/Data/In", system, "C:/SOD_OUTPUT")
    
    # NOTE: I am only using the global flag here to help specify settings this one time at startup. Change this in the future.
    global SETTINGS
    
    parser = argparse.ArgumentParser(description="Bulk compilation of laboratory instrument files.")
    parser.add_argument("--input", type=str, default="C:/Data/In", help="Input directory containing instrument files.")
    parser.add_argument("--output", type=str, default="C:/SOD_OUTPUT", help="Output directory for processed files.")
    parser.add_argument("--systems", type=str, nargs="+", default=[],
                        help="List of systems to process (space separated). Currently supported are: GRA PWAVE_L MS NGR SRM DSC RSC MSPOINT PROFILE RGB ROI XSCAN")
    
    
    parser.add_argument("--compile", action="store_true", help="If set, run make_compilation after processing.")
    parser.add_argument("--compile_only", action="store_true", help="If set, only run compilation without processing input files.")
    parser.add_argument("--settings",type=str, help="Specify a settings .json file. If none specified, used default settings.")
    
    args = parser.parse_args()
    
    try:
        if args.settings:
            with open(args.settings, "r") as f:
                temp = json.load(f)
                SETTINGS = recursively_resolve_funcs(temp)
            logger.info(f"Loaded settings from {args.settings}")
        else:
            logger.info(f"Using default application settings")
    except Exception as ex:
        logger.error(ex)
        logger.error("Error importing settings from specified json file. Using default settings")
        
    
    
    if len(args.systems) == 0:
        logger.warning("No instrument systems specified")

    if not args.compile_only:
        for system in args.systems:
            read_instrument_file(args.input, system, args.output)
    
    if args.compile:
        for system in args.systems:
            make_compilation(args.output, system)
    else:
        logger.info('Will not create compilation file for instrument system')
            
            

if __name__ == "__main__":
    
    code = "RGB"
    
    dl = DataLoader(
        path = f"C:/Data/projects/ProjectD/instrument_files", 
        pattern = rf".+\.{code}$",
        analysis = code, 
        output_dir= f"C:/Data/projects/ProjectD",
        recursive=False)
    
    instrument_files = dl._get_files(
        path=dl.path,
        pattern=dl.pattern,
        recursive=False
    )
    
    for f in instrument_files:
        dl._archive_test_files(f, hardlink=True)
     
    pattern = rf'^summary_{code.lower()}.+\.json$'
        
    summary_files = dl._get_files(
        path = dl.output_dir,
        pattern=pattern,
        recursive=True  
        )
   
    for f in summary_files:
       dl._transform_archived_test_files(f)
        
        
    
#    for f in dl._transform_archived_test_files()
#        dl._transform_archived_test_files('C:/Data/in/ProjectA/402-U1612A-3R-1-A_SHLF13015341_20240215205544__NRM/summary_402-U1612A-3R-1-A_SHLF13015341_20240215205544__NRM.json')
    
    # logger.info('Starting up')
    # main()

