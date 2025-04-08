import pandas as pd
import numpy as np
from typing import Union

def read_ngr_spe(file:str, as_dataframe:bool=False) -> Union[dict,pd.DataFrame]:
    content = None
    with open(file,"r") as f:
        # remove newlines and spaces
        content = [line.strip() for line in f]

    length = len(content)
    # parse fields

    fields = {}
    for line in content:
        if "#" in line:
            key, value = line.split("#", 1)
            fields[key.strip()] = value.strip()
    fields

    # These fields need special parsing ["$DATE_MEA:", "AP#", "$MEAS_TIM:", "$DATA:"]
    # The field is listed below one line below the field label
    for line in content:
        if "TYPE:" in line:
            fields['TYPE'] = line.split("TYPE:")[-1].strip()

    try:
        i = content.index("$DATE_MEA:")
        fields["DATE_MEA"] = content[i+1]
    except:
        pass

    try:
        i = content.index("AP#")
        fields["AP"] = content[i+1]
    except:
        pass
    
    try:
        i = content.index("PAIRED DATA#")
        fields["PAIRED DATA"] = ";".join(content[i+1:i+4])
    except:
        pass

    try:
        i = content.index("$MEAS_TIM:")
        fields["MEAS_TIM"] = content[i+1]
    except:
        pass

    i = content.index("$DATA:")

    # normally this is 1024 bins (0-1023)
    data_bins = int(content[i+1].split(" ")[-1])
    
    # shift by two,slice to end of file
    fields["DATA"] = content[i+2:data_bins]
    
    if as_dataframe:
        # pivots the spectrum into columns
        idx = np.arange(0,len(fields['DATA']))
        
        # make a dataframe from the non-spectral columns
        _f = {k: v for k, v in fields.items() if k != "DATA"}
        df = pd.DataFrame(_f, index=[0])
        
        # transpose the spectrum, concatenate the dataframes
        df = pd.concat([df, pd.DataFrame(fields['DATA'], index=idx).T], axis=1)
        return df
    else:
        return fields


def read_ngr_edge_correction_txt(file: str)->pd.DataFrame:
    first_blank_row = 0
    i = 0
    with open(file,"r") as f:
        for l in f:
            if l.strip()  == "":
                first_blank_row =  i - 1
                break
            i+=1
    
    df = pd.read_csv(file, sep='\t', nrows=first_blank_row)
    return df





if __name__ == "__main__":
    pass