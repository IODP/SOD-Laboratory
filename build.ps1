# pyinstaller should already be installed. It is accessible via the command-line.
# pip install -U pyinstaller

# The active shell working path should be SOD-Laboratory root folder
# Make the /temp/build folder manually if it doesn't exist. 
pyinstaller workflows/bulk_compilation.py --onefile --distpath temp/build/bin --workpath temp/build/build --specpath temp/build/spec


# running from SOD-Laboratory root then:
temp/build/bin/bulk_compilation.exe --help