# pyinstaller should already be installed. It is accessible via the command-line.
# pip install -U pyinstaller

# The active shell working path should be SOD-Laboratory root folder
# Make the /temp/build folder manually if it doesn't exist. 

# --add-data tag will include other files (e.g. settings.json) in build product

######## Building SODLAB ###########
# Write-Host "Building sodlab as one file..."
# pyinstaller workflows/sodlab.py `
#     --name "sodlab" `
#     --onefile `
#     --distpath temp/build/bin `
#     --workpath temp/build/build `
#     --add-data "workflows/settings.json;."
#     # --specpath temp/build/spec  `
# # Size is ~114 MB

# We are building sodlab before sodlab_ui
Write-Host "Building sodlab as one directory"
pyinstaller workflows/sodlab.py `
    --name "sodlab" `
    --onedir `
    --distpath temp/onedir/bin `
    --workpath temp/onedir/build `
    --add-data "workflows/settings.json;."
    # --specpath temp/onedir/spec `
    # --hidden-import iodp.ms # hidden imports are modules Pyinstaller will include even if they aren't explictly imported in your .py scripts. Use for dynamic loading cases.
    # --hidden-import iodp.ngr

# Size is ~40 MB

# This outputs to: .\temp\onedir\bin\sodlab\sodlab.exe 

# Copy settings file to output. Settings.json is handled by pyinstaller now.
# Copy-Item -Path .\workflows\settings.json -Destination .\temp\build\bin\sodlab
# Copy-Item -Path .\workflows\settings.json -Destination .\temp\onedir\bin\sodlab

# Write-Host "Building sodlab_gradio_ui as one file..."
# pyinstaller workflows/sodlab_gradio_ui.py `
#     --name "sodlab_ui" `
#     --onefile `
#     --distpath temp/build/bin `
#     --workpath temp/build/build `
#     --add-data "workflows/settings.json;."



####### Building SODLAB_UI #######

# These types of instructions sent the location of python modules back into powershell variables.
# The paths from these variables were then inserted into the --add-data parameter for pyinstaller
# in order to add modules only found at runtime.
# I bypass this by using a "hooks" directory and just inserted the module references there.

$gradioPath = @"
import os, gradio
print(os.path.dirname(gradio.__file__))
"@ | python

$gradioClientPath  = @"
import os, gradio_client
print(os.path.dirname(gradio_client.__file__))
"@ | python

$safehttpx  = @"
import os, safehttpx
print(os.path.dirname(safehttpx.__file__))
"@ | python

Write-Host "Building sodlab_gradio_ui as one directory..."

# NOTE: Need to use the add-data and the additional-hooks for some reason.
# probably just need to add groovy to add-data and we should be good.
pyinstaller workflows/sodlab_ui.py `
    --name "sodlab_ui" `
    --onedir `
    --distpath temp/onedir/bin `
    --workpath temp/onedir/build `
    --add-data "workflows/settings.json;." `
    --add-data "$gradioClientPath;gradio_client" `
    --add-data "$gradioPath;gradio" `
    --add-data "$safehttpx;safehttpx" `
    --additional-hooks-dir=hooks # NOTE: the hooks here is the "hooks" directory i.e. SOD-Laboratory/hooks

# this outputs to: .\temp\onedir\bin\sodlab_ui\sodlab_ui.exe 

Write-Host "Build and copy operations completed successfully."

Write-Host "Testing application(s)..."


# $time = Measure-Command { .\temp\build\bin\sodlab.exe --help }
# Write-Host "Time to invoke one-file build app: {$time}"
# ~takes about 12 seconds to load

$time = Measure-Command { .\temp\onedir\bin\sodlab\sodlab.exe --help }
Write-Host "Time to invoke one-dir build app: {$time}"
# takes about 2 seconds to load