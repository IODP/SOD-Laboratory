import pandas as pd
import numpy as np
from typing import Union

def read_avs_csv_file(file:str,as_dataframe:bool=True,mode:str='data') -> Union[dict, pd.DataFrame]:
    """Reads AVS csv files and outputs a dataframe of data, or a dataframe or dictionary of metadata.

    Args:
        file (str): A path to AVS csv file
        as_dataframe (bool, optional): If True outputs a dataframe, else a dictionary. Defaults to True.
        mode (str, optional): Either 'data' or 'metadata', specifies which set of data to return. Defaults to 'data'.

    Returns:
        Union[dict, pd.DataFrame]: _description_
    """
    content = []
    with open(file, "r", encoding='ansi') as f:
        for i, l in enumerate(f):
            t = l.strip()
            # skip rows with only commas
            if set(t) == {','}:
                continue
            content.append(t)
            
            
    start = 0
    # end will always be the last line
    end = len(content) 
    cleaned = []  
    for i, l in enumerate(content):
        # Beginning of data table
        if l.startswith('date,speed'):
            start = i
            
        cleaned.append(l.split(','))
                

    metadata = {}

    metadata['device_no'] = cleaned[8][1]
    metadata["barcode_scan"] = ",".join(cleaned[9][8:12])
    metadata['method'] = cleaned[0][2]

    metadata['operator'] = cleaned[start][8]
    metadata['vane'] = cleaned[start+1][8]
    metadata['penetration_direction'] = cleaned[start+2][8]
    metadata['rotation_rate'] = cleaned[start+3][8]
    metadata['top_interval'] = cleaned[start+4][8]

    if not as_dataframe:
        return metadata
    
    if mode == 'data':
        df_data = pd.DataFrame(cleaned[start+1:end], columns=cleaned[start])
        df_data  = df_data.iloc[:,0:6]
        
        # insert metadata for each row
        df = pd.concat(
            [pd.DataFrame(metadata,index=range(df_data.shape[0])),
            df_data],
            axis=1
        )
       
        return df

    # Note: use reset_index when slicing out row, otherwise pd.concat() joins on the index and creates ghost rows
    if mode == 'metadata':
        df_units = pd.DataFrame(cleaned[1:7][:start])
        df_units.columns = df_units.loc[0]
        df_units = df_units.iloc[1:,:6].reset_index(drop=True)
        
        # insert metadata for each row
        df = pd.concat(
            [pd.DataFrame(metadata,index=range(df_units.shape[0])),
            df_units],
            axis=1
        )
        
        return df


    return pd.DataFrame()


if __name__ == "__main__":
    pass