import pandas as pd
import numpy as np
from typing import Union


def read_pxrf_spm_file(file: str) -> pd.DataFrame:
    content = []
    with open(file, 'r', encoding ='utf-16') as f:
        for line in f.readlines():
            content.append(line.strip().split('\t'))

    df = pd.DataFrame(content)
    # Readings start after "TimeStamp"
    timestamp_idx = int(df[df.iloc[:,0] == "TimeStamp"].index[0])
    reading_idx = timestamp_idx+1
    
    # The data readings must be shifted to the right by one column
    df.iloc[reading_idx:,1:] = df.iloc[reading_idx:,:-1]
    df.iloc[reading_idx:,0] = None
    return df