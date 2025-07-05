
import pandas as pd
import numpy as np
from typing import Union
import io
from iodp import utils
import re
import os



def read_ms_csv(file:str) -> pd.DataFrame:
    
    content = None
    with open(file, 'r') as f:
        content = [line.strip() for line in f]
        
    
    nrows = None
    # Find the first empty line
    for idx, line in enumerate(content):
        if line == '':
            nrows = idx
            break
    
    # zero-based index
    nrows = nrows - 1
    # Read lines up to the first empty line into a DataFrame
    df = pd.read_csv(file,nrows=nrows)
    
    
    try:
        i = content.index("Parameters:")

        fields = {}
        for l in content[i+1:]:
            # NOTE: After values here may be a units field. I am disregarding them because the units typically are in the key.
            key, val, *_ = l.split(',')
            fields[key] = val
            

        # pivots the spectrum into columns
        idx = np.arange(0,len(fields))
        
        # make a dataframe from the non-spectral columns
        _f = {k: v for k, v in fields.items()}
        df_fields = pd.DataFrame(_f, index=[0])
        df_fields = pd.concat([df_fields] * df.shape[0], ignore_index=True)

        
        # transpose the spectrum, concatenate the dataframes
        df = pd.concat([df, df_fields], axis=1)
       
  
    except Exception as e:
        print(e)
        print("Could not parse Parameters footer")
        
        
    return df




if __name__ == "__main__":
    
    file = 'PhysicalProperties/data/input/MSLOOP/raw_400-u1603a-1h-1_2308241457173_ms.csv'
    df = read_ms_csv(file)