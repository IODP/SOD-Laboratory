# IODP

This module contains tools for importing raw data files from numerous IODP instrument systems as `pandas.DataFrame` objects.

Code specific to instrument systems are partitioned within their own modules, e.g. `ngr.py`,`gra.py`, etc. Functionality shared among systems are stored in the `utils` module.


# Installation

The `iodp` module should be installed using the `-e` flag so that updates to the underlying scripts will be automatically applied without having to uninstall/reinstall the module.

```shell
# from within the SOD-Laboratory folder

cd ./SOD-Laboratory

pip install -e iodp
```

# Example Usage

```python
# Example reading a Natural Gamma Radiation Spectrum file.

import os
import pandas as pd
from iodp import ngr

path = "path_to_file"
file = "395-u1554g-2h-1_sect12466821_20230628123026/395-U1554G-2H-1_0cm_SECT12466821_20230628123026_NaI_8.SPE"
file_path = os.path.normalize(os.path.join(path, file))

# return the contents as a dataframe
spe = ngr.read_ngr_spe(file, as_dataframe=True)
spe
```
# Compatibility

The `iodp` module was designed for instrument files acquired circa 2024-2025. Compatibility issues with earlier IODP expeditions may arise. 

# Documentation:

View the API Reference Documention for important libraries below:
- Pandas: https://pandas.pydata.org/
- Numpy: https://numpy.org/