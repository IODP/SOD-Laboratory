import pandas as pd
import numpy as np
from typing import Union


def read_pwavel_csv(file) -> Union[dict, pd.DataFrame]:
    """Reads a pwave-l file. The waveform occupies the last columns and the raw files do not have headers for those columns.
    """
    
    df = pd.read_csv(file, header=None, skiprows=1)
    cols = pd.read_csv(file, header=None, nrows=1).loc[0]
    cols = [x.strip() for x in cols]
    
    # waveform col begins in last position of cols. Ignore the header, just use ints.
    cols = cols[0:-1] + list(range(df.shape[-1] - len(cols) + 1))
    df.columns = cols
    return df


if __name__ == "__main__":
    pass