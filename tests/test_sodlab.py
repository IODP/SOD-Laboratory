import iodp
import os
from pathlib import Path
import workflows.sodlab as bc


def create_testset():
    testset = bc.TestSet()
    
    assert testset is not None
    
    
def test_pytest():
    assert True == True
    
    
    
def test_verify_ifile_abs():
    
    print(os.getcwd())
    
    # Use pathlib for robust relative path handling
    test_file_dir = Path(__file__).parent  # Gets the directory where this test file is located
    gra_file = test_file_dir / "data" / "400-U1603A-1H-1_20230824145601.GRA"
    
    filekeys = ['config']
    files = bc._verify_ifile(str(gra_file), filekeys, force_relative=False)
    
    assert len(files) == 2
    
    key, val = files[0]
    
    assert key == 'config'
    assert val == os.path.normpath('c:\\ims\\config_wrmsl\\i_pi_gra.ini')
    
    key, val = files[1]
    assert key == 'instrument_file'
    assert val == os.path.normpath(gra_file)