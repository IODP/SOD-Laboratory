import sys
import os
from importlib import reload

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from functools import partial

from iodp import utils, ngr, pwavel, srm, shmsl, ms

import re
import zipfile
import logging
import io

from pathlib import Path

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
      #  logging.FileHandler("bulk_compilation.log", mode='a')
    ]
)

logger = logging.getLogger(__name__)

file_graph = {
    "PWAVE_L": {
        "analysis": "PWAVE-L",
        "instrument_file": {
            "func": utils.read_instrument_file,
            "kwargs": {},
            "add_depths" : {
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
            
            kwargs_spec = file_graph[extension]['instrument_file'].get("kwargs",None)
            instrument_file_tabular = utils.read_instrument_file(instrument_file_path, as_dataframe=True, **kwargs_spec)
            
            # Add depths is specified
            specs = file_graph[extension].get("instrument_file", None)
            depths_spec = None
            if specs:
                depths_spec = file_graph[extension]['instrument_file'].get("add_depths",None)
            if depths_spec:             
                instrument_file_tabular = utils.add_depths_to_dataframe(
                    df=instrument_file_tabular,
                    offset_col=depths_spec['offset_col'],
                    sample_number_col=depths_spec['sample_number_col'],
                    is_textid_col=depths_spec['is_textid_col']    
                )
                
            
        except Exception as ex:
            logger.error(f"Error reading instrument file: {instrument_file}")
        
    
        
        # Transform the summary file: 
        analysis = file_graph[extension]['analysis']
        raw_filename = os.path.split(instrument_file_path)[-1]
        raw_filename_root, ext = os.path.splitext(raw_filename)
        destination_path = os.path.normpath(
            os.path.join(destination, analysis, test_folder, f"{analysis}_instrument_file_{raw_filename_root}") + ".csv"
            )
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        instrument_file_tabular.to_csv(destination_path,index=False)
        
        # Get the list of file keys within files with supplied extension
        file_ref_keys = list(file_graph[extension]['files'].keys())
        
        
        # Iterate through keys. Apply specific file transform to each file. Save transformed file copies to new location
        for file_key in file_ref_keys:

            full_file_path = instrument_file[file_key]
            
            if full_file_path is None:
                logger.info(f"instrument file: {file}, {file_key}: Has no file reference.")
                continue
            
            logger.info(f"Processing {file_key}: {full_file_path}")
            
            
            transform_fn = file_graph[extension]['files'][file_key]['func']
            trans_kwargs = file_graph[extension]['files'][file_key]['kwargs']
            
            temp = None
            if transform_fn is None:
                logger.info(f"Will simply copy file to new location.")
            else:
                logger.info(f"Will transform file using function: {transform_fn} with kwargs: {trans_kwargs}")
                
                try:
                    temp = transform_fn(full_file_path, **trans_kwargs)
                    
                    depths_spec = file_graph[extension]['files'][file_key].get("add_depths",None)
                    if depths_spec:
                        
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


if __name__ == "__main__":

    read_instrument_file("C:/Data/In", "DSC", "C:/SOD_OUTPUT")
