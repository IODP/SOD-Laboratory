from typing import Union
import re 

import pandas as pd
import numpy as np


def read_spinner_txt_file(file) -> pd.DataFrame: 

    # spinner text files conveniently used a section header flag.
    # we can split on it
    SOH = '\x01'

    content = []
    with open(file, 'r', encoding='ansi') as f:
        temp = f.read().split(SOH)

    for l in temp:
        m = l.strip('\n').split('\n')
        # disregard empty lines
        if len(m)>1:
            content.append(m)


    # content is a list of lists
    # each inner list is a "section"
    # each section formatting is identical to all other sections,
    # except for the last section, which may be mistakenly truncated.
    records = []

    for i, section in enumerate(content):
        data = {}
        # 0: sample info
        vals = section[0].split()
        data["text_id"] = vals[0]
        data["treatment"] = vals[2]
        data["date"] = vals[3]

        # 2: aximuth and dip angles
        vals = section[2].split()
        data['azimuth'] = vals[1]
        data['dip'] = vals[2]

        # 3: parameters
        vals = section[3].split()

        data['foliation_plane_azimuth_dip'] = vals[1]
        data['foliation_plane_dip'] = vals[2]
        data['lineation_trend'] = vals[3]
        data['lineation_plunge'] = vals[4]

        data['data'] = {}

        # 7: x-z reading
        vals = section[7].split()
        data['data'][vals[0]] = {'x': vals[1], 'y': None, 'z': vals[2]}

        # 8: y-z reading
        vals = section[8].split()
        data['data'][vals[0]] = {'x': None, 'y': vals[1], 'z': vals[2]}

        # 9: x-y reading
        vals = section[9].split()
        data['data'][vals[0]] = {'x': vals[1], 'y': vals[2], 'z': None}

        # 11: means row has the arithmetic means of the preceding section of individual magnetic moments.
        vals = section[11].split()
        data['mean_x'] = vals[0]
        data['mean_y'] = vals[1]
        data['mean_z'] = vals[2]

        # 12: modulus row has intensity, units, precision in degrees and percentage
        vals = section[12].split()

        data['intensity'] = vals[1]
        data['precision_deg'] = vals[4].rstrip('°')
        data['precision_pct'] = vals[5].rstrip('%')

        # 14: operational parameters
        vals = section[14].split()
        data['orientation_parameter_1'] = vals[1]
        data['orientation_parameter_2'] = vals[2]
        data['orientation_parameter_3'] = vals[3]
        data['orientation_parameter_4'] = vals[4]

        # 16: specimen values
        vals = section[16].split()
        data['declination_specimen'] = vals[2]
        data['inclination_specimen'] = vals[3]

        
        # 17: geographic values
        # Note: the last section of the file may not have this part
        try:
            vals = section[17].split()
            data['declination_geographic'] = vals[1]
            data['inclination_geographic'] = vals[2]
        except:
            print(f"reading {i} does not have geographic section")
        
        records.append(data)

    # make a dataframe, forget the raw data, only considering means
    df = pd.DataFrame(records).drop(columns=['data'])
    return df





def read_spinner_jr6_file(file: str) -> pd.DataFrame:
        
    # Note: the beginning of the text_id is usually cut off for the id to fit into the character length.
    # E.g. CUBE13016931 becomes "E13016931"
    # Must find out the labels for columns 5 and 17.
    columns = [
        "text_id",
        "treatment_type",
        "mean_moment_x",
        "mean_moment_y",
        "mean_moment_z",
        "column5",
        "azimuth",
        "dip",
        "foliation_plane_azimuth_dip",
        "foliation_plane_dip",
        "lineation_trend",
        "lineation_plunge",
        
        "orientation_parameter_p1",
        "orientation_parameter_p2",
        "orientation_parameter_p3",
        "orientation_parameter_p4",
        "column17"
        ]

    # Issue with .jr6 files is that the number of characters per entry are fixed and may replace the delimiter at times.
    # Especially for inclination/declination columns
  

    content = []
    r = r"\s+"
    with open(file, "r") as f:
        
        for l in f:
            s = re.split(r'\s+', l.strip())
            content.append(s)

    # need to verify the inclination/declination values have been split.
    chk_indices = [2,3,4]

    # pat matches items like -12.3-6.76, 6.87-16.43, 8-9, there must be two numbers separated by a hyphen with no spaces.
    pat = r'(?P<val1>-?\d+(\.\d+)?)(?P<val2>-\d+(\.\d+)?)'
    for i, row in enumerate(content):
        for ind in chk_indices:
            res = re.match(pat, row[ind])
            
            if res:
                # overwrite current entry with first val
                row[ind] = res.groupdict()['val1']
                # insert second val and shift remaining vals by 1 position
                row.insert(ind+1, res.groupdict()['val2'])
            

            
            
    return pd.DataFrame(content, columns=columns)
    