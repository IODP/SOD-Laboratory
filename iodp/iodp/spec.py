import pandas as pd
import numpy as np
from typing import Union

def read_spec_csv_file(file:str, as_dataframe:bool=True, profile_only:bool=False ) ->pd.DataFrame:
    content = []
    with open(file, "r") as f:
        for l in f:
            t = l.strip()
            if len(t) > 0:
                content.append(t)
        
    data = {}

    for row in content[:25]:
        if row.count(',') > 0:
            key, val = row.split(',',maxsplit=1)
            val = val.split(',')[0].strip()
        elif row.count(':') > 0:
            key, val = row.split(':')
        else:
            key = row
            val = None
            
        key = key.strip().lower().replace(" ", "_")
        data[key] = val
    
    # Note: handles split path.
    # This occurs if the batch name column too large. Need to add back in the stripped space.
    if '' in data:
        data['batch_name'] += " " + data['']
        data.pop('') 
    
    # remove certain keys:
    # these are artifacts of the parsing
    rm_keys = ['advanced_reads_report','analysis','instrument_settings']
    for k in rm_keys:
        data.pop(k)
        

    # The spectrophotometer data spans row 27 until the "Results Flags Legend" is present in row.
    start = 27
    end = start
    for row in content[start:]:
        if "Results Flags Legend" in row:
            break
        end += 1
    
    
    # parse readings
    temp = []
    for row in content[start:end]:
        temp.append(row.split(','))
        
    columns = [x.strip() for x in content[start-2].split(',')]
    df = pd.DataFrame(temp, columns=columns)
    if '' in df.columns: df.pop('')
    
    for col in df.columns:
        df[col] = df[col].str.strip()
    
    if profile_only:
        return df
    
    if not as_dataframe:
        for col in df.columns:
            data[col.lower()] = list(df[col].str.strip().values)
        return data

            
    df_header = pd.DataFrame(data,index=range(df.shape[0]))
    df = pd.concat(
        [df_header, df],
        axis=1
    )
    
    return df