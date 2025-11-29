#
# Calls PyInstaller to build CLI
#

pip install -r requirements.txt

$BuildDirName = "build"
$SourceDir = $PSScriptRoot
$BuildDir = [io.path]::combine($PSScriptRoot, $BuildDirName)

if (-Not (Test-Path -Path $BuildDir)) {
    New-Item -Force -ItemType Directory -Path "$BuildDir"
}

Push-Location "$BuildDir"

$logDataFile = "$SourceDir\log_data_list.txt"
$trackerStatesFile = "..\..\..\..\..\..\Definitions\tracker_states.json"
$recordStatesFile = "..\..\..\..\..\..\Definitions\record_states.json"

pyinstaller --name CLI -F "$SourceDir\command_line.py" --distpath "$BuildDir" --workpath "$BuildDir\temp" --specpath "$BuildDir" --add-data "${logDataFile}:." --add-data "${trackerStatesFile}:." --add-data "${recordStatesFile}:."

Pop-Location
