
# Check if Anaconda is installed
if (-not (Get-Command conda)) {
    Write-Host "Anaconda is not installed"
}
else {
    conda --version
}

# Check if the "sod" environment exists
if ((conda env list | Select-String -Pattern "sod") -ne $null) {
    Write-Host "The 'sod' environment exists."
}
else {
    Write-Host "The 'sod' environment does not exist."
}

# Verify if the 'sod' environment targets Python 3.12
if ((conda env list | Select-String -Pattern "sod") -ne $null) {
    $pythonVersion = conda run -n sod python --version 2>&1
    if ($pythonVersion -match "Python 3\.13") {
        Write-Host "The 'sod' environment targets Python 3.13."
    }
    else {
        Write-Host "The 'sod' environment does not target Python 3.13. Detected version: $pythonVersion"
    }
}
