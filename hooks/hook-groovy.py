from PyInstaller.utils.hooks import collect_data_files

# Include Groovy internal files if installed
try:
    import groovy
    datas = collect_data_files("groovy")
except ImportError:
    pass