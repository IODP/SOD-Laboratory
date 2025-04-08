
from logging import warn
import sys
import os
import warnings
from functools import reduce
import re

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import configparser
import colour


#region Parsing .csv files
def read_shmsl_rsc_csv(file, spectra_only:False):

    df = pd.read_csv(file)

    if spectra_only:
        # spectral data are all columns after this position
        
        pos = None
        try:
            pos = df.columns.get_loc('time (us)')
        except:
            pos = df.columns.get_loc('time(us)')
        

        # offset is in first column, 

        offset_col = df.columns.get_loc('offset(cm)')

        cols = [offset_col] + list(range(pos+1, len(df.columns)))
        df = df.iloc[:, cols].copy()
        df.columns = df.columns.str.strip()
        return df
    
    
    df.columns = df.columns.str.strip()
    return df


def read_shmsl_rsc_cal_csv(file, spectra_only:False):

    df = pd.read_csv(file)

    if spectra_only:
        # spectral data are all columns after this position
        
        pos = None
        try:
            pos = df.columns.get_loc('time (us)')
        except:
            pos = df.columns.get_loc('time(us)')

        cols = list(range(pos+1, len(df.columns)))

        return df.iloc[:, cols].copy()
    
    return df

#endregion
#region Parsing .RSC files

def _get_start_end_indices(pattern, content):
    m = re.compile(pattern)

    start = 0
    end = len(content)
    indices = []

    for index in range(0, len(content)):

        line = content[index]
        if m.match(line):
            indices.append(index)
            #print(line)
            #print(index)

    assert len(indices) == 2

    # print(indices)

    indices = sorted(indices)
    
    # start and end indices for section
    return (indices[0], indices[1])

def _parse(start:0, end, content, form):
    """
        Search content lines for the keys in form. Assign values to keys
    """
    if end is None:
        end = len(content)

    for x in form:
        pattern = f"{x} = (?P<value>.+)"
        #print(pattern)
        m = re.compile(pattern)

        vals = []

        for line in content[start:end+1]:
            t = m.search(line)

            if t is None:
                continue
        
            vals.append(t.group('value'))

        # Will assign a list of multiple matches if they exist
        if len(vals) == 0:
            form[x] = None
        elif len(vals) == 1:
            form[x] = vals[0]
        else:
            form[x] = vals
        
    return form

def _parse_multi(start:0, end, content, pattern):
    if end is None:
        end = len(content)

    m = re.compile(pattern)

    vals = []
    for line in content[start:end+1]:
            t = m.search(line)

            if t is None:
                continue
        
            # groupdict is a dictionary of all the groups and match values
            vals.append(t.groupdict())

    return vals



def read_shmsl_rsc(file)->pd.DataFrame:
    
    
    if not file.endswith('.RSC'):
        warnings.warn("The file extension does not match the expected '.RSC' extension.", UserWarning)
    
    # NOTE: The keys in template resolve to regex
    template = {
    "</?HEADER>": {
                    "user": None,
                    "text_id": None,
                    "instrument": None,
                    "instrument_group": None,
                    "observed_length": None,
                    "comment": None
                },
    "</?SINGLE>":{
        "geometry": None,
        "illuminant": None,
        "observer": None,
        "calibration_valid": None
    },
    "</?MULTI>":{
        "offset": None 
    },
    "</?FILE>":{
        "rsc_norm": None,
        "rsc_raw": None,
        "config": None
    },
    "</?NOTES>":{
        "positions_excluded": None
    }
    }

    content = None
    with open(file, "r") as f:
        content = f.readlines()
        
        
    content = None
    with open(file, "r") as f:
        content = f.readlines()

    
    if content[0] != "RSC":
        warnings.warn("File preamble does not contain 'RSC'")
        
    pat = r"(?P<datetime>.+ UTC), (?P<labelid>.+)"
    m = re.compile(pat)
    t = m.search(content[2])
    df_pre = pd.DataFrame([t.groupdict()])

    pat_multi = r"offset =\s+(?P<offset>.+), cielab_l_star=(?P<cielab_l_star>.+), cielab_a_star=(?P<cielab_a_star>.+), cielab_b_star=(?P<cielab_b_star>.+), hue=(?P<hue>.+), chroma=(?P<chroma>.+), tristimulus_x=(?P<tristimulus_x>.+), tristimulus_y=(?P<tristimulus_y>.+), tristimulus_z=(?P<tristimulus_z>.+), sample_time=(?P<sample_time>\d+)"
    for pattern in template:
        start, end = _get_start_end_indices(pattern,content)
        if pattern == "</?MULTI>":
            template[pattern] = _parse_multi(start,end,content,pat_multi)
        else:
            template[pattern] = _parse(start,end, content=content,form=template[pattern] )


    fields = ["</?HEADER>", "</?SINGLE>", "</?FILE>", "</?NOTES>"]


    # Combine all dictionaries in the list
    combined_dict = reduce(lambda d1, d2: d1 | d2, [template[y] for y in fields])
    combined_dict   

    multi = pd.DataFrame(template["</?MULTI>"]).astype(float)
    combo = pd.DataFrame(combined_dict, index=[0])

    # Replicate df2 to match the number of rows in df1
    df2_replicated = pd.concat([combo] * len(multi), ignore_index=True)
    df_pre = pd.concat([df_pre]* len(multi), ignore_index=True)
    # Combine df1 and the replicated df2
    combined_df = pd.concat([multi, df2_replicated], axis=1)
    combined_df = pd.concat([df_pre, combined_df], axis=1)

    return combined_df

def read_shmsl_mspoint(file)->pd.DataFrame:
    
    
    if not file.endswith('.MSPOINT'):
        warnings.warn("The file extension does not match the expected '.MSPOINT' extension.", UserWarning)
    
    # NOTE: The keys in template resolve to regex
    template = {
    "</?HEADER>": {
                    "user": None,
                    "text_id": None,
                    "instrument": None,
                    "instrument_group": None,
                    "observed_length": None,
                    "comment": None
                },
    "</?SINGLE>":{
        "ms_units": None,
        "ms_correction": None,
        "ms_zero": None,
        "zero_timestamp": None,
        "ms_sample_integration_time": None,
        "ms_zero_integration_time": None
    },
    "</?MULTI>":{
        "offset": None 
    },
    "</?FILE>":{
        "aux_file": None,
        "config": None
    },
    "</?NOTES>":{
        "positions_excluded": None
    }
    }
        
    content = None
    with open(file, "r") as f:
        content = f.readlines()

    # First line may end in spaces or \n character.
    if not "MSPOINT" in content[0]:
        warnings.warn("File preamble does not contain 'MSPOINT'")
        
    pat = r"(?P<datetime>.+ UTC), (?P<labelid>.+)"
    m = re.compile(pat)
    t = m.search(content[2])
    df_pre = pd.DataFrame([t.groupdict()])

    pat_multi = r"offset =(\s+)?(?P<offset>.+),(\s+)?magnetic_susceptibility =(\s+)?(?P<magnetic_susceptibility>.+),(\s+)?timestamp =(\s+)?(?P<timestamp>.+),(\s+)?time_since_zero =(\s+)?(?P<time_since_zero>.+)"
    for pattern in template:
        start, end = _get_start_end_indices(pattern,content)
        if pattern == "</?MULTI>":
            template[pattern] = _parse_multi(start,end,content,pat_multi)
        else:
            template[pattern] = _parse(start,end, content=content,form=template[pattern] )


    fields = ["</?HEADER>", "</?SINGLE>", "</?FILE>", "</?NOTES>"]


    # Combine all dictionaries in the list
    combined_dict = reduce(lambda d1, d2: d1 | d2, [template[y] for y in fields])
    combined_dict   

    multi = (
        pd.DataFrame(template["</?MULTI>"])
        .astype({"offset": float, "magnetic_susceptibility": float, "time_since_zero":float})
             )
    
    combo = pd.DataFrame(combined_dict, index=[0])

    # Replicate df2 to match the number of rows in df1
    df2_replicated = pd.concat([combo] * len(multi), ignore_index=True)
    df_pre = pd.concat([df_pre]* len(multi), ignore_index=True)
    # Combine df1 and the replicated df2
    combined_df = pd.concat([multi, df2_replicated], axis=1)
    combined_df = pd.concat([df_pre, combined_df], axis=1)

    return combined_df

def read_shmsl_mspoint_csv(file:str)->pd.DataFrame:
    before_parameters = []
    after_parameters = []
    parameters_found = False

    content = None
    with open(file,"r") as f:
        content = f.readlines()
    
    for line in content:
        if line.strip() == "\n":
            continue
        
        if "Parameters:" in line:
            parameters_found = True
            
        if parameters_found:
            after_parameters.append(line)
        else:
            before_parameters.append(line)

    before_parameters, after_parameters

    warnings.warn("Splitting lines on commas may produce mal-formed DataFrames if commas exist in table elements")
    before_parameters = [line.split(",") for line in before_parameters]

    # strip newlines and spaces
    cols = [x.strip() for x in before_parameters[0]]
    df = pd.DataFrame(before_parameters[1:], columns=cols)

    # Split on the first comma only
    after_parameters_split = [line.strip().split(",", 1) for line in after_parameters[1:]]

    # Use the first row as column names and the rest as data
    after_parameters_df = pd.DataFrame(after_parameters_split, columns=['key','value'])
    after_parameters_df['key'] = after_parameters_df['key'].str.replace('\n', '', regex=False)

    after_parameters_df = after_parameters_df.set_index('key').T
    df_pre = pd.concat([after_parameters_df] * len(df), ignore_index=True)
    combined_df = pd.concat([df_pre, df], axis=1)
    
    # fix datatypes here:
    combined_df = (
        combined_df.assign(
            **{
            "offset(cm)" : lambda _df: _df["offset(cm)"].replace(" ", None)
        })
        .astype({
            "offset(cm)": float,
            "raw_meter" : float,
            "time since zero (sec)": float,
            "susceptibility": float
            
        })
    )

    
    return combined_df


def read_shmsl_profile(file) -> pd.DataFrame:
    if not file.endswith('.PROFILE'):
        warnings.warn("The file extension does not match the expected '.PROFILE' extension.", UserWarning)
        
    # NOTE: The keys in template resolve to regex
    template = {
    "</?HEADER>": {
                    "user": None,
                    "text_id": None,
                    "instrument": None,
                    "instrument_group": None,
                    "observed_length": None,
                    "comment": None
                },
    "</?FILE>":{
        "profile": None,
        "config": None

    },
    "</?NOTES>":{
        "positions_excluded": None
    }
    }

    content = None
    with open(file, "r") as f:
        content = f.readlines()

    
    if content[0] != "PROFILE":
        warnings.warn("File preamble does not contain 'PROFILE'")
        
    pat = r"(?P<datetime>.+ UTC), (?P<labelid>.+)"
    m = re.compile(pat)
    t = m.search(content[2])
    df_pre = pd.DataFrame([t.groupdict()])
    
    
    for pattern in template:
        start, end = _get_start_end_indices(pattern,content)
        template[pattern] = _parse(start,end, content=content,form=template[pattern] )


    fields = ["</?HEADER>","</?FILE>", "</?NOTES>"]


    # Combine all dictionaries in the list
    combined_dict = reduce(lambda d1, d2: d1 | d2, [template[y] for y in fields])
    combined_dict   

    
    df_combined = pd.DataFrame(combined_dict, index=[0])
    
    # Replicate rows in the dataframe to match other df
    # actually produces a new dataframe of x rows by concatenating a 1 row dataframe x times.
    df_pre = pd.concat([df_pre] * len(df_combined), ignore_index=True)
    
    combined_df = pd.concat([df_pre, df_combined], axis=1)
    return combined_df
    
def read_shmsl_profile_csv(file:str)->pd.DataFrame:
    warnings.warn("As of 4/2/2025 there is one column name less than the total number of columns. Import disregards last column which seems like it is a constant.")

    df = (
        pd.read_csv(file,index_col=False)
      
    )
    return df

def read_shmsl_ini(file):
    config = configparser.ConfigParser(interpolation=None)
    
    text = config.read(file, encoding='utf-8')

    # for section in config.sections():
    #     try:
    #         print(f"[Section: {section}]")
    #         for key, value in config.items(section):
    #             print(f"{key} = {value}")
    #         print()
    #     except Exception as ex:
    #         print(ex)
    #         continue

    df_config = (pd.DataFrame([(i, config[k][i]) for k in config.keys() for i in config[k]])
                 .set_index(0)
                 .rename(columns={1: "value"})
                 .rename_axis("key")
                 )
    
    return df_config, config

#endregion

def tristimulus_xyz_calculation(df):
    if 'offset' in df.columns:
        shift = 1
        if df.columns[0] != 'offset':
            raise Exception("Offset column is not the first column.")
    elif 'offset(cm)' in df.columns:
        shift = 1
        if df.columns[0] != 'offset(cm)':
            raise Exception("Offset column is not the first column.")
    else:
        shift = 0  
    
    
    # dataframe pro
    wavelengths = df.iloc[0, shift:].index.values.astype(float)

    # does not include 1st col which contains "offset"
    # scale reflectance 0-1
    reflectance = df.iloc[:,shift:].values /100

    print(f"max wavelength: {wavelengths.max()}")
    print(f"min wavelength: {wavelengths.min()}")
    print(f"max reflectance: {reflectance.max()}")
    print(f"min reflectance: {reflectance.min()}")

    illuminant = colour.SDS_ILLUMINANTS['D65'].copy()
    illuminant_interpolated = illuminant[wavelengths].copy()

    # bandwidth is 2 nm
    bandwidth = 2

    cmfs_id = "CIE 1931 2 Degree Standard Observer"
    # cmfs_id = 'CIE 1964 10 Degree Standard Observer'
    
    cmfs = colour.MSDS_CMFS[cmfs_id].copy()
    cmfs_interpolated = cmfs[wavelengths].copy()

    (cmfs_interpolated * illuminant_interpolated.reshape((165,-1)) * bandwidth).shape

    print(f"shape reflectance: {reflectance.shape}")
    print(f"shape illuminant: {illuminant_interpolated.shape}")
    print(f"shape cmfs: {cmfs_interpolated.shape}")

    # dimension 1 in cmfs is for Tristimulus Y
    k = np.divide(100, (np.sum(cmfs_interpolated[:,1] * illuminant_interpolated * bandwidth)))
    print(f"k proportionality: {k}")
    print(f"bandwidth: {bandwidth}")

    XYZ = k * np.dot(reflectance * illuminant_interpolated * bandwidth, cmfs_interpolated)

    print(f"max XYZ: {XYZ.max()}")
    print(f"min XYZ: {XYZ.min()}")

    df_XYZ = (pd.DataFrame()
              .assign(
                  offset = df['offset(cm)'],
                  X = XYZ[:,0],
                  Y = XYZ[:,1],
                  Z = XYZ[:,2],
                  )
              )
   
    
    return df_XYZ


#region plotting
def _dataframe_has_offset_column(df:pd.DataFrame) -> bool:
    """Checks for a column named "offset" or "offset(cm)"

    Args:
        df (pd.DataFrame): Input dataframe of wavelength columns. May or may not contain an "offset" columns. Raises an ex

    Returns:
        bool: Returns true of "offset" or "offset(cm)" appear in the column list
    """
    cols = df.columns
    if "offset" in cols:
        
        return True
    if "offset(cm)" in cols:
        return True
    return False

    
def plot_reflectance(df:pd.DataFrame, title:str=None, ylabel:str='signal', legend:bool=False, labels:list=None)->None:
    
    wavelengths = df.columns.values.astype(float)
    
    # check there are enough labels for the records in the dataframe
    
    if labels is not None:
        if len(labels) != df.shape[0]:
            raise Exception("The number of labels is incompatible with the dataframe shape. Adjust or remove labels entirely.")
        
    
    fig, ax = plt.subplots(1,1,figsize=(20,5))
    
    
    idx_label = 0
    for idx, row in df.iterrows():
        
        if labels is not None:
            label = labels[idx_label]
        else:
            label = None
        
        ax.plot(wavelengths,
                    df.iloc[idx,:].values, 
                    label=f"{label}", color='b')
            
        idx_label+=1

    print(min(wavelengths))
    print(max(wavelengths))
    ticks = np.linspace(start=min(wavelengths), stop=max(wavelengths), num=15)  # 15 evenly spaced ticks
    
    if legend:
        plt.legend()
    
    if title:
        plt.title(title)
        
    plt.xticks(ticks)
    plt.xlabel('wavelength (nm)')
    plt.ylabel(ylabel)
    plt.show()
    
    
#endregion

if __name__ == "__main__":
    pass