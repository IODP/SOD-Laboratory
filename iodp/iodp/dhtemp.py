import pandas as pd
import numpy as np
from typing import Union

def read_dhtemp_dat_file(file:str, profile_only:bool=False) -> pd.DataFrame:
    content = []
    with open(file, "r") as f:
        for l in f:
            content.append(l.strip())
            
    data = {}

    # parse lines from 'LoggerIdentifier' to 'TemperatureCubic'
    for i in content[2:14]:
        key, val = i.split(":", maxsplit=1)
        key = key.strip().lstrip("# ").lower().replace(" ","_")
        val = val.strip()

        data[key] = val

    c = [x.split() for x in content[16:]]
    df = pd.DataFrame(c[1:], columns=c[0])
    if profile_only:
        return df
    
    df_header = pd.DataFrame(data,index=range(df.shape[0]))
    df = pd.concat(
        [df_header, df],
        axis=1
        )

    return df


def read_dhtemp_txt(file:str, time_shift:bool=False, profile_only:bool=False) -> pd.DataFrame:
    """Parses and return DHTEMP .dat file data as a dataframe. May include header information. Option to return the "Results vs time-shift" or the "Data and model" portions of the .dat.

    Args:
        file (str): The file path to a DHTEMP .dat file
        time_shift (bool, optional): Returns the "Results vs time-shift" portion of the .dat file, else returns the "Data and model" portion. Defaults to False.
        profile_only (bool, optional): Show only the profile data columns, ignore the header. Defaults to False.

    Returns:
        pd.DataFrame: A dataframe of the .dat file contents
    """
    
    content = []
    with open(file, "r") as f:
        for l in f:
            t = l.strip()
            
            if len(t) == 0:
                continue
            
            if t.startswith("="):
                continue
            
            content.append(t)
            
    data = {
        "version": content[0],
        "comment": content[1],
    }

    for row in content[2:25]:
        
        key, val = row.split(":\t")
        # replacing the exponenents too
        key = (key.strip().lower()
            .replace(" ", "_")
            .replace("³", "^3")
            .replace("°", "deg")
            )
        val = val.strip()
        
        data[key] = val

    # Parse the "Results vs time-shift" section
    start = 27
    next_section = None
    i = start
    for row in content[start:]:
        if row.startswith("Time (s)"):
            next_section = i
            break
        i+=1

    df = None
    
    if time_shift:
        c = [x.split("\t") for x in content[27:next_section]]
        df = pd.DataFrame(data=c[1:], columns=c[0])
    else:
        c = [x.split("\t") for x in content[next_section:]]
        df = pd.DataFrame(data=c[1:], columns=c[0])

    if profile_only:
        return df

    df_header = pd.DataFrame(data, index=range(df.shape[0]))
    df = pd.concat(
        [df_header, df],
        axis=1
    )
    return df