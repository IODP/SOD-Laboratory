from typing import Union
import re

import pandas as pd
import configparser
import numpy as np

def read_instrument_file(file:str, as_dataframe:bool=False) -> Union[dict,pd.DataFrame]:

    # Read file content
    content = []
    with open(file,"r") as f:
        for line in f:
            content.append(line.strip())
  

    fields = {}
    
    # Datetime stamp and label id are in the 3rd row (2nd index pos)
    pat = r"(?P<datetime>.+ UTC), (?P<labelid>.+)"
    m = re.compile(pat)
    t = m.search(content[2])
    
    if t:
        fields = t.groupdict()
    
    # Pattern matches complete lines like: ["<HEADER>", "<MULTI>", "<FILE>"]
    pattern = r"^<(?P<section>\w+-?\w+)>$"

    # start parsing from 4th row (3rd index pos)
    # close_pat is the complement to the section. Example: if section is <FILE>, the closing pattern is </FILE>
    close_pat = None
    match = None
    section = None
    for l in content[3:]:
        match = re.match(pattern, l)

        # Enter a section
        if match:
            section = match['section']
            close_pat = fr"^</{section}>$"
            continue
    
        # We are not in a section, just skip line
        if section == None:
            continue
        
        # Exit a section
        match = re.match(close_pat, l)
        if match:
            continue
        
        # skip if line is empty
        if len(l) == 0:
            continue
        
        # Note: many track systems use the "MULTI" section. Only the SRM uses MULTI-LEADER, MULTI-TRAILER, etc
        multi_sections = ['MULTI-LEADER', 'MULTI', 'MULTI-TRAILER', 'MULTI-DRIFT']
        
        # Parse from within the section, get key/value pairs. MULTI sections have multiple key/value pairs
        if not section in multi_sections:
        # Handles non <MULTI> like section content
            key, val = l.split("=",maxsplit=1)
            fields[key.strip()] = val.strip()
            continue
        
        # Handles <MULTI> like section content
        if section in multi_sections:
            if not section in fields:
                fields[section] = []
            
            # split multi, first by comma then by first appearance of "="
            # list comprehension will remove all empty artifacts from splitting on commas
            arr = dict(map(lambda x: map(str.strip, x.split("=", 1)), [item for item in l.split(",") if len(item)>0]))
            fields[section].append(arr)
    
    # return the dictionary of values instead of dataframe
    if not as_dataframe:
        return fields
    
    # Return results as a dataframe
    # NOTE: The various SRM MULTI sections all follow the same format, they can be combined into one dataframe
    # get all the multi-like sections in fields
    
    # Convert parent dict into a DataFrame (except 'multi' sections)
    base_data = {k: v for k, v in fields.items() if not k in multi_sections}
    
    # get the multi sections that appear in the fields
    # the ordering here is important. the multi_sections list is ordered appropriately based on .SRM files.
    # other instruments solely use <MULTI> so ordering is irrelevant
    common = [section for section in multi_sections if section in fields]
   

    # returns a single row dataframe
    if len(common) == 0:
        # index of 0 here indicates this is df of one row
        return pd.DataFrame(base_data, index=[0])
    
    # returns a multi row dataframe
    multi_df = pd.DataFrame()
    for section in common:
        multi_data = fields[section]
        
        # stack multi dataframes
        multi_df = pd.concat(
            [multi_df,
                pd.DataFrame(multi_data)], axis=0)

    # Duplicate the base data for each row
    base_df = pd.DataFrame([base_data] * len(multi_df))

    # Concatenate horizontally
    df = pd.concat([base_df.reset_index(drop=True), multi_df.reset_index(drop=True)], axis=1)

    return df
    
        

def read_instrument_ini(file, as_dataframe:bool=False) -> Union[configparser.ConfigParser, pd.DataFrame]:
    config = configparser.ConfigParser(interpolation=None)
    
    _ = config.read(file, encoding='utf-8')

    # for section in config.sections():
    #     try:
    #         print(f"[Section: {section}]")
    #         for key, value in config.items(section):
    #             print(f"{key} = {value}")
    #         print()
    #     except Exception as ex:
    #         print(ex)
    #         continue

    if as_dataframe:
        return (pd.DataFrame([(i, config[k][i]) for k in config.keys() for i in config[k]])
                 .set_index(0)
                 .rename(columns={1: "value"})
                 .rename_axis("key")
                 )
    
    
    return config



#region Tools
def convolve(data:np.ndarray, windowsize:int=3) -> np.ndarray:
    # normally bins is 0-1023, so 1024 bins
    bins = np.arange(0,len(data))

    # performing a 1D convolution to represent a running average of length = window
    # "same" retains output array shape, handling boundary effects.
    avg = np.convolve(data,(1/windowsize)*np.ones(windowsize),"same")
    
    return avg
    
    

#endregion



if __name__ == "__main__":
    pass