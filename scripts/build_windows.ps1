param([switch]$Installer)
$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

python -m pip install -r requirements/desktop-build.txt
if ($LASTEXITCODE -ne 0) { throw "Build dependency installation failed" }
python -m pip install --no-deps .
if ($LASTEXITCODE -ne 0) { throw "Application installation failed" }
if ($Installer) {
    python scripts/build_desktop.py --package
} else {
    python scripts/build_desktop.py
}
if ($LASTEXITCODE -ne 0) { throw "Desktop build failed" }
Write-Host "Bundle: $repoRoot\dist\VISOR\VISOR.exe"
