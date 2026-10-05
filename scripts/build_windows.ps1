$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

python -m pip install -e ".[build]"
python scripts/generate_icon.py
python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --name VISOR `
    --paths src `
    --icon src/visor/assets/visor.ico `
    --add-data "src/visor/assets/visor.ico;visor/assets" `
    --add-data "src/visor/assets/visor.svg;visor/assets" `
    --add-data "src/visor/assets/icons;visor/assets/icons" `
    src/visor/__main__.py

Write-Host "Build complete: $repoRoot\dist\VISOR\VISOR.exe"
