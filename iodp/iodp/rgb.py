import pandas as pd
import numpy as np
from typing import Union

import pandas as pd


def read_rgb_high_res_dat(file:str, as_dataframe:bool=True) -> pd.DataFrame:
    
    content = None
    with open(file,'r') as f:
        content = [x.strip() for x in f.readlines()]
        
   
    metadata = {}
    
    metadata['labelid'] = content[0].strip()
    metadata['timestamp'] = content[1].strip().strip(',')
    
    fields_start = 2
    data_start = None
    
    for idx, line in enumerate(content[fields_start:]):
        if line == '':
            data_start = fields_start + idx + 1
            break
        key, val = line.strip().split("=")
        
        metadata[key] = val.strip()

    data_lines = content[data_start:]
    
    if not data_lines:
        raise ValueError("No data found after metadata section.")

    header = data_lines[0].split('\t')
    rows = [line.split('\t') for line in data_lines[1:] if line]

    df = pd.DataFrame(rows, columns=header)

    if as_dataframe:
        df_meta = pd.DataFrame(metadata, index=[0])
        df_meta = pd.concat([df_meta] * df.shape[0], ignore_index=True)
        df = pd.concat([df_meta, df], axis=1)
        return df
    
    
    metadata['data'] = df
    return df

    
if __name__ == "__main__":
        
    file = "PhysicalProperties/data/input/RGB/202-1237B-2H-1-A_SHLF15723332_20250701195923_RGB.dat"
    df = read_rgb_high_res_dat(file, as_dataframe=True)
    
    print(df)


    
    