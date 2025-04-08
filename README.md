# SOD-Laboratory

This repository provides code and how-to examples for processing raw data from instrument systems owned and operated by Scientific Ocean Drilling at Texas A&M University. Many of these systems were housed on the R/V JOIDES Resolution overseen by the Joides Science Operator (JRSO) as part of the International Ocean Discovery Program and were shipped back to shore laboratories in College Station, TX after the completion of the ship demobilization.

Folders are organized by laboratory. The iodp module contains Python code used within many of the Jupyter Notebooks.

# Installation 

```powershell
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

cd ./SOD-Laboratory

# from within the SOD-Laboratory folder:
# The iodp module must be a subfolder.
# pip install with the "-e" flag instals the module as an editable file location
# This helps with active development
pip install -e iodp

```
