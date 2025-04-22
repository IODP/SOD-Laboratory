import pandas as pd
import numpy as np
from typing import Union


def read_xrf_spe_file(file:str, as_dataframe:bool=True) -> Union[pd.DataFrame, dict]:

    content = []

    with open(file, "r") as f:
        for line in f:
            content.append(line.strip())
            
    # problem is if a value is null the line is not included.
    # so cannot hardcode positions
    ref = {
        "$Core_ID:": "core_id",
        "$Section_ID:": "section_id",
        "$Depth:": "depth",
        "$Run_ID:": "run_id",
        "$X_Position:": "x_position",
        "$Y_Position:": "y_position",
        "$Replicate_ID:": "replicate_id",
        "$Slit_DC:": "slit_downcore",
        "$Slit_CC:": "slit_crosscore",
        "$TotalCPS:": "total_cps",
        "$SPEC_ID:": "spec_id",
        "$USER_ID:": "user_id",
        "$ACC_VOLT:": "acc_volt",
        "$TUBE_CUR:": "tube_current",
        "$MEAS_TIM:": "measurement_time",
        "$DATE_MEA:": "date_measured",
    }

    data = {}

    # Parse header
    reading_start = 0
    for i, line in enumerate(content):
        if line in ref:
            # insert the custom column names from ref
            data[ref[line]] = content[i+1].strip()
        
        # The data section is positioned at the base of the file.
        # exit loop upon encountering    
        if line == '$DATA:':
            reading_start = i+2
            break

    # Parse the spectral data. May have a variable number of columns
    readings = []
    for line in content[reading_start:]:
        readings.append(line.split())
    
    # return data in dictionary format
    if not as_dataframe:
        data['data'] = readings
        return data

    # Concatenate dataframes
    df = pd.DataFrame(readings)
    df_header = pd.DataFrame(data,index=range(df.shape[0]))
    df = pd.concat([
        df_header,
        df
    ], axis=1)
    
    return df