import pandas as pd
import numpy as np
from typing import Union



def read_xrd_uxd_file(file:str, as_dataframe=True) -> Union[dict,pd.DataFrame]:
    content = []
    with open(file, 'r') as f:
        for line in f:
            content.append(line.strip())

    data = {}
    reading_start = 0
    for idx, line in enumerate(content):
        if line.startswith("_"):
            
            vals = [val.strip() for val in line.split("=", maxsplit=1)]
            if len(vals) > 1:
                data[vals[0]] = vals[1]
            else:
                data[vals[0]] = None
        
        if line == "; Cnt2_D1":
            reading_start = idx+1
            break

    readings = content[reading_start:]
    if not as_dataframe:
        data['spectrum'] = readings
        return data
        
    df = pd.DataFrame(readings, columns=['spectrum'])
    df_header = pd.DataFrame(data, index=range(df.shape[0]))
    df = pd.concat([
        df_header,
        df
    ], axis=1)

    return df