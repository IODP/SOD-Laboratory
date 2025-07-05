import pandas as pd
import numpy as np
from typing import Union
import io
from iodp import utils
import zipfile
import re
import os


def read_ngr_spe(file:Union[str|io.BytesIO], as_dataframe:bool=False) -> Union[dict,pd.DataFrame]:
    content = None
    
    # Note: The io objects here are primarily used if the file reference originates from a zip archive.
    if isinstance(file,str):
        with open(file,"r") as f:
            # remove newlines and spaces
            content = [line.strip() for line in f]
    elif isinstance(file, io.BytesIO):
        text = file.read().decode('utf-8')
        content = [line.strip() for line in text.splitlines()]
    elif isinstance(file, io.StringIO):
        content = [line.strip() for line in f]
    else:
        raise Exception("Input filetype is incompatible.")

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

    # normally this is 1024 bins (0-1023). Zero-based index so add 1.
    data_bins = int(content[i+1].split(" ")[-1]) + 1
    
    # shift now to start of data channels
    i = i + 2
    
    # slice to end of file
    fields["DATA"] = content[i:i+data_bins]
    
    assert len(fields['DATA']) == data_bins
    
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


def read_ngr_edge_correction_txt(file: Union[str, io.BytesIO])->pd.DataFrame:
    
    content = None
    # Note: The io objects here are primarily used if the file reference originates from a zip archive.
    if isinstance(file,str):
        with open(file,"r") as f:
            # remove newlines and spaces
            content = [line.strip() for line in f]
    elif isinstance(file, io.BytesIO):
        text = file.read().decode('utf-8')
        content = [line.strip() for line in text.splitlines()]
        # remember to reset the buffer to the beginning after reading it.
        file.seek(0)
    elif isinstance(file, io.StringIO):
        content = [line.strip() for line in f]
    else:
        raise Exception("Input filetype is incompatible.")
    
    first_blank_row = 0
    i = 0
     
    for l in content:
        if l.strip()  == "":
            first_blank_row =  i - 1
            break
        i+=1
    
    df = pd.read_csv(file, sep='\t', nrows=first_blank_row)
    return df

def read_zip_file(zip_path: str, **kwargs):
    """Transforms the contents of a NGR .zip into .csv files. 

    Args:
        zip_path (str): NGR .zip file path
        output_path (str): A full path for an output .zip file.
    """
    with zipfile.ZipFile(zip_path, 'r') as input_zip:
    
        output_buffer = io.BytesIO()
        
        with zipfile.ZipFile(output_buffer, 'w', zipfile.ZIP_DEFLATED) as output_zip:
            
            # print("zip contains the following files:")
            # for f in input_zip.infolist():
            #    print(f"\t{f.filename}")
            
                  
            #
            # 
            #########
            # Calibration spectra
            #########
            pat = r"^CALIB_\d+_NaI_\d.SPE$"

            matched_files = [f for f in input_zip.infolist() if re.match(pat, f.filename)]
            
            df = pd.DataFrame()
            
            # looping through the matched files and using the zip archive to open the file contents
            for file_info in matched_files:
                with input_zip.open(file_info) as f:
                    file_bytes = f.read()
                    bytes_buffer = io.BytesIO(file_bytes)
                    temp = read_ngr_spe(bytes_buffer, as_dataframe=True)
                    df = pd.concat([df,temp])
        
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            
            output_zip.writestr("ngr_calibration_spectra.csv", csv_buffer.getvalue())
            
            #
            #
            #########
            # Spectral Measurements
            #########
            pat = r"^.+_SECT\d+_\d+_NaI_\d.SPE$"

            matched_files = [f for f in input_zip.infolist() if re.match(pat, f.filename)]
            
            df = pd.DataFrame()
            
            # looping through the matched files and using the zip archive to open the file contents
            for file_info in matched_files:
                with input_zip.open(file_info) as f:
                    file_bytes = f.read()
                    bytes_buffer = io.BytesIO(file_bytes)
                    temp = read_ngr_spe(bytes_buffer, as_dataframe=True)
                    df = pd.concat([df,temp])
        
            csv_buffer = io.StringIO()
            df = df.sort_values(by=['DET', 'OFFSET cm'])
            df.to_csv(csv_buffer, index=False)
            
            output_zip.writestr("ngr_measurement_spectra.csv", csv_buffer.getvalue())
            
            #
            #
            #########
            # Standard Background Measurements
            #########
            
            pat = r"^STND-NGRBACK_.+_\d+_NaI_\d.SPE$"
       
            matched_files = [f for f in input_zip.infolist() if re.match(pat, f.filename)]
            
            df = pd.DataFrame()
            
            # looping through the matched files and using the zip archive to open the file contents
            for file_info in matched_files:
                with input_zip.open(file_info) as f:
                    file_bytes = f.read()
                    bytes_buffer = io.BytesIO(file_bytes)
                    temp = read_ngr_spe(bytes_buffer, as_dataframe=True)
                    df = pd.concat([df,temp])
        
            csv_buffer = io.StringIO()
            df = df.sort_values(by=['DET'])
            df.to_csv(csv_buffer, index=False)
            
            output_zip.writestr("ngr_detector_background_spectra.csv", csv_buffer.getvalue())

            #
            #
            #########
            # Detector Edge Correction
            #########
            
            pat = r"^NGR_EDGE_CORRECTION_\d+.txt$"
       
            matched_files = [f for f in input_zip.infolist() if re.match(pat, f.filename)]
            
            df = pd.DataFrame()
            
            # looping through the matched files and using the zip archive to open the file contents
            for file_info in matched_files:
                with input_zip.open(file_info) as f:
                    file_bytes = f.read()
                    bytes_buffer = io.BytesIO(file_bytes)
                    temp = read_ngr_edge_correction_txt(bytes_buffer)
                    df = pd.concat([df,temp])
        
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            
            output_zip.writestr("ngr_edge_correction.csv", csv_buffer.getvalue())
            
            
            
            #
            #
            #########
            # NGR Initialization file
            #########

            pat = r"^I_PI_NGR\d+.INI$"
       
            matched_files = [f for f in input_zip.infolist() if re.match(pat, f.filename)]
            
            df = pd.DataFrame()
            
            # looping through the matched files and using the zip archive to open the file contents
            for file_info in matched_files:
                with input_zip.open(file_info) as f:
                    file_bytes = f.read()
                    bytes_buffer = io.BytesIO(file_bytes)
                    temp = utils.read_instrument_ini(bytes_buffer, as_dataframe=True)
                    df = pd.concat([df,temp])
        
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            
            output_zip.writestr("ngr_initialization_file.csv", csv_buffer.getvalue())
            
            #
            #
            #########
            # NGR Summary file
            #########

            pat = r"^.+_(SECT|SHLF)\d+_\d+.CSV$"
       
            matched_files = [f for f in input_zip.infolist() if re.match(pat, f.filename)]
            
            df = pd.DataFrame()
            
            # looping through the matched files and using the zip archive to open the file contents
            for file_info in matched_files:
                with input_zip.open(file_info) as f:
                    file_bytes = f.read()
                    bytes_buffer = io.BytesIO(file_bytes)
                    temp = pd.read_csv(bytes_buffer)
                    df = pd.concat([df,temp])
        
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            
            output_zip.writestr("ngr_summary_file.csv", csv_buffer.getvalue())
    
             
        # moves buffer position to beginning
        output_buffer.seek(0)
        
        
        # export the buffer to file if specified
        if "output_path" in kwargs:
            with open(kwargs["output_path"], "wb") as f:
                f.write(output_buffer.read())       

        return output_buffer
    


if __name__ == "__main__":
    
    # for debugging
    print(os.getcwd())
    
    file = "PhysicalProperties/data/input/NGR/395-u1554g-2h-1_sect12466821_20230628123026/395-U1554G-2H-1_0cm_SECT12466821_20230628123026_NaI_8.SPE"
    read_ngr_spe(file,as_dataframe=True)