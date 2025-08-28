# pyinstaller should already be installed. It is accessible via the command-line.
# pip install -U pyinstaller

# The active shell working path should be SOD-Laboratory root folder
# Make the /temp/build folder manually if it doesn't exist. 

Write-Host "Building sodlab as one file..."
# ~114 MB
pyinstaller workflows/bulk_compilation.py --name "sodlab" --onefile --distpath temp/build/bin --workpath temp/build/build --specpath temp/build/spec


Write-Host "Building sodlab as one directory"
# ~40 MB
pyinstaller workflows/bulk_compilation.py --name "sodlab" --onedir --distpath temp/onedir/bin --workpath temp/onedir/build --specpath temp/onedir/spec


# Copy settings file to output
Copy-Item -Path .\workflows\settings.json -Destination .\temp\build\bin\sodlab
Copy-Item -Path .\workflows\settings.json -Destination .\temp\onedir\bin\sodlab

Write-Host "Build and copy operations completed successfully."

Write-Host "Testing application(s)..."


$time = Measure-Command { .\temp\build\bin\sodlab.exe --help }
Write-Host "Time to invoke one-file build app: {$time}"
# ~takes about 12 seconds to load

Measure-Command { .\temp\onedir\bin\sodlab\sodlab.exe --help }
Write-Host "Time to invoke one-dir build app: {$time}"
# takes about 2 seconds to load