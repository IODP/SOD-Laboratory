import pandas as pd
import numpy as np
from typing import Union


def read_pwavec_lvm_file(file, only_profile:bool=False) -> pd.DataFrame:
    content = []
    with open(file, "r") as f:
        for l in f:
            t = l.strip()
            if len(t) > 0:
                content.append(t)

    data = {
        "writer_version": content[1].split(",")[-1],
        "reader_version": content[2].split(",")[-1],
        "operator": content[8].split(",")[-1],
        "description": content[9].split(",", maxsplit=1)[-1],
        "date": content[10].split(",")[-1],
        "time": content[11].split(",")[-1],
        "channels": content[14].split(",",maxsplit=1)[-1].rstrip(','),
        "samples": content[15].split(",",maxsplit=1)[-1].rstrip(','),
        "delta_x": content[20].split(",",maxsplit=1)[-1].rstrip(',')  
    }
            
    df = pd.DataFrame(
        list(map(lambda x: x.split(","), content[23:])),
        columns=content[22].split(",")[0:2]
                )

    if only_profile:
        return df

    df = pd.concat(
        [
            pd.DataFrame(data, index=range(df.shape[0])),
            df
        ],
        axis=1
    )
    
    return df