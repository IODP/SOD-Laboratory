# pyinstaller should already be installed. It is accessible via the command-line.
# pip install -U pyinstaller

# The active shell working path should be SOD-Laboratory root folder
# Make the /temp/build folder manually if it doesn't exist. 

# --add-data tag will include other files (e.g. settings.json) in build product

Write-Host "Building sodlab as one file..."
pyinstaller workflows/sodlab.py `
    --name "sodlab" `
    --onefile `
    --distpath temp/build/bin `
    --workpath temp/build/build `
    --add-data "workflows/settings.json;."
    # --specpath temp/build/spec  `
# Size is ~114 MB

Write-Host "Building sodlab as one directory"
pyinstaller workflows/sodlab.py `
    --name "sodlab" `
    --onedir `
    --distpath temp/onedir/bin `
    --workpath temp/onedir/build `
    --add-data "workflows/settings.json;."
    # --specpath temp/onedir/spec `

# Size is ~40 MB

# Copy settings file to output. Settings.json is handled by pyinstaller now.
# Copy-Item -Path .\workflows\settings.json -Destination .\temp\build\bin\sodlab
# Copy-Item -Path .\workflows\settings.json -Destination .\temp\onedir\bin\sodlab

Write-Host "Build and copy operations completed successfully."

Write-Host "Testing application(s)..."


$time = Measure-Command { .\temp\build\bin\sodlab.exe --help }
Write-Host "Time to invoke one-file build app: {$time}"
# ~takes about 12 seconds to load

$time = Measure-Command { .\temp\onedir\bin\sodlab\sodlab.exe --help }
Write-Host "Time to invoke one-dir build app: {$time}"
# takes about 2 seconds to load