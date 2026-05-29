from PyInstaller.utils.hooks import collect_data_files

# Include all SafeHTTPX files (including internal version.txt)
datas = collect_data_files("safehttpx")
