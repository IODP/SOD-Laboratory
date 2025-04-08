# SOD-Laboratory

![SOD-Laboratory Overview](./assets/graphics/i-gcr.png)


This repository provides code and how-to examples for processing raw data from instrument systems owned and operated by Scientific Ocean Drilling at Texas A&M University. Many of these systems were housed on the R/V JOIDES Resolution overseen by the Joides Science Operator (JRSO) as part of the International Ocean Discovery Program and were shipped back to shore laboratories at the Gulf Core Repository (GCR) College Station, TX after the completion of the ship demobilization.

Folders are organized by laboratory. The `iodp` module contains Python code used within many of the Jupyter Notebooks. Consult the Installation section below to configure a Python environment.



# Information

- IODP website: https://iodp.tamu.edu/index.html
- i-GCR website: https://gcr.tamu.edu/

### Instrument Systems:
- Live manuals: https://tamu-eas.atlassian.net/wiki/spaces/LMUG/overview
- Archived instrument manuals: [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.14917864.svg)](https://doi.org/10.5281/zenodo.14917864)

### Data Access:

Expedition data reports and raw data:
- LORE Reports: https://web.iodp.tamu.edu/LORE/
- Proceedings Volumes: https://iodp.tamu.edu/publications/proceedings.html

Data packaged by expedition: 
- Expedition lists: https://iodp.tamu.edu/database/zenodo.html
- IODP Zenodo Community: https://zenodo.org/communities/iodp/records

### Feedback
- Send questions/requests to database@iodp.tamu.edu.


# Installation 

```shell
# ensure python is installed.
python --version

# ensure anaconda is installed
conda --version

# ensure git is installed
git --version

# create a new python virtual environment called "sod"
conda create --name sod python=3.13

# clone remote repo to local folder
git clone "remote location"

# activate virtual environment
conda activate sod

# from within the SOD-Laboratory folder:
# The iodp module must be a subfolder.
cd ./SOD-Laboratory

pip install -r iodp/requirements.txt

# pip install with the "-e" flag installs the module as an editable file location
# This helps with active development
pip install -e iodp

```

# Funding

- `NSF-OCE 2412279`: Closeout of JOIDES Resolution IODP Expedition Obligations and Operation of an Instrumented Gulf Coast Repository, US National Science Foundation. https://www.nsf.gov/awardsearch/showAward?AWD_ID=2412279

- `NSF-OCE 1326927`: Management and Operations of the JOIDES Resolution as a Facility for the International Ocean Discovery Program (IODP), US National Science Foundation. https://www.nsf.gov/awardsearch/showAward?AWD_ID=1326927

- `NSF-OCE 0352500`: System Integration Contractor for the Integrated Ocean Drilling Program, US National Science Foundation. https://www.nsf.gov/awardsearch/showAward?AWD_ID=0352500