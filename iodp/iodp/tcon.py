import pandas as pd
import numpy as np
from typing import Union


def read_tcon_dwl_file(file, profile_only:bool=False) -> pd.DataFrame:
    
    # The # of header lines
    lines = 8
    
    with open(file, "r", encoding='utf-16') as f:
        content = [next(f).strip() for _ in range(lines)]
    

    data = {
        "name": content[0],
        "ini_file": content[1].split(",")[0],
        "teka_version": content[1].split(",")[1],
        "date": content[1].split(",")[-1],
        "comment": content[2],
        "heating_power_watt_per_min": content[3].split("=")[-1].strip(),
        "slope" : content[4].split(" ")[2],
        "slope_neg" : content[4].split(" ")[3],
        "slope_std" : content[4].split(" ")[6],
        "t" : content[4].split(" ")[9],
        "lc" : content[4].split(" ")[12],
        "val1": content[5],
        "val2": content[6],
        "val3": content[7]
    }    
    
    
    df_data = pd.read_csv(file, sep= r"\s+", skiprows=9, encoding="utf-16", header=None)
    df_data.columns = ["temp_degC", "time_sec", "resistence_ohm"]
    
    if profile_only:
        return df_data
    
    df_header = pd.DataFrame(data, index=range(df_data.shape[0]))
    df = pd.concat([df_header, df_data], axis=1)
    
    return df


def read_tcon_erg_file(file, profile_only:bool=False) -> pd.DataFrame:
    content = []
    with open(file, "r", encoding="utf-16") as f:
        for l in f:
            content.append(l.strip())
        
    data = {
        "file_name" :content[0].split(":")[-1].strip(),
        "comment" :content[1].strip(),
        "from_start_time_sec": content[4].split(" ")[0],
        "to_start_time_sec": content[5].split(" ")[0],
        "int_length_min_sec": content[6].split(" ")[0],
        "end_time_sec": content[7].split(" ")[0],
        "let": content[8].split(" ")[0],
        "contact_val": content[9].split(" ")[0]
        
    }
    
    # Note: passing no arg to split will split on multiple spaces
    df = pd.DataFrame([x.split() for x in content[12:]])
    df.columns = content[10].split()
    
    if profile_only:
        return df
        
    df_data = pd.DataFrame(data,index=range(df.shape[0]))
    
    df = pd.concat([df_data, df], axis=1)
    return df

def read_tcon_dat_file(file:str) -> pd.DataFrame:
    content = []
    with open(file, "r", encoding="utf-16") as f:
        for l in f:
            content.append(l.strip())
            

    df = pd.DataFrame(
        list(map(lambda x: x.split(maxsplit=9), content[2:])), 
        columns=content[0].split()
        )
    return df


if __name__ == "__main__":
    pass