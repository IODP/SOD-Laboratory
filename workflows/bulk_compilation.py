import sys
import os
from importlib import reload, import_module

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from functools import partial

from iodp import utils, ngr, pwavel, srm, shmsl, ms, rgb

import re
import zipfile
import logging
import io

from pathlib import Path
import argparse
import json

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

parser = argparse.ArgumentParser(description="Bulk compilation of laboratory instrument files.")
parser.add_argument("--input", type=str, default="C:/Data/In", help="Input directory containing instrument files.")
parser.add_argument("--output", type=str, default="C:/SOD_OUTPUT", help="Output directory for processed files.")
parser.add_argument("--systems", type=str, nargs="+", default=[],
                    help="List of systems to process (space separated). Currently supported are: GRA PWAVE_L MS NGR SRM DSC RSC MSPOINT PROFILE RGB ROI XSCAN")
parser.add_argument("--compile", action="store_true", help="If set, run make_compilation after processing.")
parser.add_argument("--compile_only", action="store_true", help="If set, only run compilation without processing input files.")
parser.add_argument("--settings",type=str, help="Specify a settings .json file. If none specified, used default settings.")


SETTINGS = {
    "PWAVE_L": {
        "analysis": "PWAVE_L",
        "instrument_file": {
            "func": utils.read_instrument_file,
            "kwargs": {},
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
            "kwargs": {},
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
            "kwargs": {},
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
            "kwargs": {},
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
            "kwargs": {}
            
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
            "kwargs": {},
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
            "kwargs": {},
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
            "kwargs": {},
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
            "kwargs": {},
            "add_depths" : {
                "active": False,
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
            "kwargs": {},
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
            "kwargs": {"drop_fields":['calib_dark_raw', 'calib_white_raw']}
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
            
            # Currently BytesIO are for zip files from the NGR
            if isinstance(temp, io.BytesIO):
                destination_path = os.path.normpath(
                    os.path.join(destination, analysis, test_folder, raw_filename_root) + ".zip"
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
    
    logger.info('Starting up')
    main()

