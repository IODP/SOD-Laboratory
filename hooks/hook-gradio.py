
from PyInstaller.utils.hooks import collect_data_files

# Include all Gradio templates, static files, and simple templates
datas = collect_data_files("gradio")