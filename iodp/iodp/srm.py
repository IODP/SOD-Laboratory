from typing import Union

import pandas as pd
import numpy as np



def read_srm_csv(file:str) -> pd.DataFrame:
    content = []
    with open(file,'r') as f:
    
        for l in f:
            content.append(l.strip())

    data = {}     
    for l in content[1:7]:
        key, val = l.split(':',maxsplit=1)
        data[key.strip()] = val.strip()


    # section try length, only one comma
    key, val = content[8].split(',',maxsplit=1)
    data[key.strip()] = val.strip()

    # top offset row, contains many commas
    vals = content[9].split(',')
    data[vals[0].strip()] = vals[1].strip()

    df = pd.DataFrame([x.split(',') for x in content[11:]], columns=content[10].split(','))

    df_header = pd.DataFrame(data, index=range(df.shape[0]))

    return pd.concat(
        [df, df_header],
        axis=1)
