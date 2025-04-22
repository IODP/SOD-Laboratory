import pandas as pd
import numpy as np
from typing import Union


def read_kappa_asc_file(file:str) -> Union[pd.DataFrame, dict]:

    # asc files use the old form_feed character to separate sections.
    # the formatting of all sections are identical.
    FORM_FEED = '\x0c'
    with open(file,'r', encoding='ansi') as f:
            # split on the form feed character
            content = f.read().split(FORM_FEED)
            # parse within each section, split on newlines, only returns lines having more than 1 element
            content = [ [x for x in l.strip().split('\n') if len(x) > 0] for l in content]
            # only keep sections with lines, this handles the empty lines at the end of the file
            content = [x for x in content if len(x) > 0]

    print(len(content))
    measurements = []

    for lines in content:
        data = {}

        vals = lines[0].split()
        data['textid'] = vals[0]
        data['measurement'] =  " ".join(vals[1:4])
        data['program'] = " ".join(vals[4:])

        vals = lines[2].split()
        data['azimuth'] = vals[1]
        data['operational_parameter1'] = vals[4]
        data['operational_parameter2'] = vals[5]
        data['operational_parameter3'] = vals[6]
        data['operational_parameter4'] = vals[7]
        data['nominal_value'] = vals[10]
        vals

        vals = lines[3].split()
        vals
        data['dip'] = vals[1]
        data['demag_factor'] = vals[5]
        data['holder'] = vals[7]
        data['act_vol'] = vals[10]

        for key, val in zip(lines[4].split(), lines[5].split()):
                data[key] = val.strip()

        vals = lines[8].split()
        data['field_a/m'] = " ".join(vals[0:2])
        data['mean_susc'] = vals[2]
        data['std_err_pct'] = vals[3]
        data['tests_for_anisotropy_F'] = vals[4]
        data['tests_for_anisotropy_F12'] = vals[5]
        data['tests_for_anisotropy_F23'] = vals[6]

        vals = lines[11].split()
        data['norm_principal_susc'] = vals[0:3]
        data['95_pct_confidence_angles_E12'] = vals[3]
        data['95_pct_confidence_angles_E23'] = vals[4]
        data['95_pct_confidence_angles_E13'] = vals[5]


        vals = lines[12].split()
        data['norm_principal_susc_err'] = vals[1:]

        vals = lines[14].split()
        for key, val in zip(lines[14].split(), lines[15].split()):
                data["anisotropy_factor_"+key] = val


        vals = lines[17].split()
        data['declination_spec_system_prin_dir'] = vals[2:5]
        data['declination_spec_system_normed_tensor'] = vals[5:]
        vals = lines[18].split()
        data['inclination_spec_system_prin_dir'] = vals[2:5]
        data['inclination_spec_system_normed_tensor'] = vals[5:]
        vals = lines[19].split()
        data['declination_geo_system_prin_dir'] = vals[2:5]
        data['declination_geo_system_normed_tensor'] = vals[5:]

        vals = lines[20].split()
        data['inclination_geo_system_prin_dir'] = vals[2:5]
        data['inclination_geo_system_normed_tensor'] = vals[5:]

        vals = lines[21].split()
        data['date'] = vals[0]
            
        measurements.append(data)
        
    return pd.DataFrame(measurements)