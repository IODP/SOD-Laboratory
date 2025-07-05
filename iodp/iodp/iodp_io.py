from shutil import ExecError
import requests
import json

import os
import pandas as pd



def _get_lims_sample_metadata(sample_ids):
    
    # Documentation for API: https://github.com/tamu-edu/dor-iodp-services-limsr/blob/main/src/main/java/pita/ws/SamplesOnlyGet.java
    base_url = "https://web.iodp.tamu.edu/limsR/SamplesOnlyGet-SOD"
    
    # Alternative base URL can collect Test and Result info:
    # base_url = "https://web.iodp.tamu.edu/limsM/SamplesGet-SOD"


    results = []
    for i in range(0, len(sample_ids), 20):
        batch_ids = sample_ids[i:i+20]
       # print(batch_ids)
        params = {
            # Ensure batch_ids are strings before joining
            "sampleids": ",".join(str(sid) for sid in batch_ids),
            
            # NOTE: "11311" depth scale is CSF-A. "11331" depth scale is CSF-B 
            "depthfilters": "[\"scale_id= \'11311\'\"]"
        }
        response = requests.get(base_url, params=params)
        # print("Requesting URL:", response.url)
        if response.status_code == 200:
            results.extend(response.json())
        else:
            response.raise_for_status()
    return results

def _parse_sample_metadata(sample:str):
    
        key = sample["sample_number"]
        data = {
        "sample_number" : key,
        "text_id" : sample["text_id"]
        }
        
        if not "depths" in sample:
            raise Exception(f"{key}: Sample metadata does not contain depth key.")
        if len(sample["depths"]) == 0:
            raise Exception(f"{key}: Sample metadata does not contain depths.")
        if len(sample["depths"]) > 1:
            raise Exception(f"{key}: Multiple CSF-A depths exist for the same sample.")
        
        assert len(sample['depths']) == 1
        
        data['top'] = sample['depths'][0]['top']
        data['bot'] = sample['depths'][0]['bot']
        data['scale_id'] = sample['depths'][0]['scale_id']
        
        return (key, data)
        
        

def get_sample_metadata(sample_ids) -> dict:
    
    # the final list can only contain numerics
    sample_ids = [sid for sid in sample_ids if isinstance(sid, (int, str)) and str(sid).isdigit()]
    sample_ids = list(set(sample_ids))
    
    
    metadata = _get_lims_sample_metadata(sample_ids)
    datadict = {}
    for sample in metadata:
        key, value = _parse_sample_metadata(sample)
        if key in datadict:
            raise Exception(f"Multiple entries exist for {key}")
        datadict[key] = value
        
    return datadict

    
if __name__ == "__main__":
  
      
    sample_ids = [13015321, 13015351, 13015381] 
    
    datalist = get_sample_metadata(sample_ids)

    df = pd.DataFrame(datalist)
    print(df.shape)
    
    

    
    
        
        
  