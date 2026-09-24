@echo off
SETLOCAL ENABLEEXTENSIONS
cd /d "%~dp0"

set ROOT=%CD%
set PY=%ROOT%\.venv\Scripts\python.exe

echo =========================================
echo VISOR rebuild and smoke-check
echo =========================================

if not exist "%PY%" (
    echo ERROR: Python venv not found at %PY%
    echo Create it first with:
    echo   py -m venv .venv
    echo Then rerun this script.
    pause
    exit /b 1
)

echo [1/5] Upgrading packaging tools...
"%PY%" -m pip install --upgrade pip setuptools wheel

echo [2/5] Installing build dependencies...
"%PY%" -m pip install pyinstaller pillow

echo [3/5] Installing learned matcher dependency...
"%PY%" -m pip install "git+https://github.com/cvg/LightGlue.git"

echo [4/5] Smoke-checking the current source and learned engine availability...
"%PY%" -c "import os; os.environ['QT_QPA_PLATFORM']='offscreen'; from visor.ui.main_window import MainWindow; import inspect; print('source_import=OK'); print('window_class=', MainWindow.__name__); from visor.learned_engines import is_learned_available, is_xfeat_available; import lightglue; print('learned_available=', is_learned_available()); print('xfeat_available=', is_xfeat_available()); print('lightglue_import=OK')"
if errorlevel 1 (
    echo ERROR: source or learned-engine smoke check failed.
    pause
    exit /b 1
)

echo [5/5] Closing any stale VISOR processes and rebuilding...
taskkill /F /IM VISOR.exe >nul 2>&1
if exist "%ROOT%\build\VISOR" (
    rmdir /s /q "%ROOT%\build\VISOR"
)
if exist "%ROOT%\dist\VISOR" (
    rmdir /s /q "%ROOT%\dist\VISOR"
)
if exist "%ROOT%\build\VISOR.exe" (
    del /q "%ROOT%\build\VISOR.exe"
)

"%PY%" -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --windowed ^
    --name VISOR ^
    --paths "%ROOT%\src" ^
    --icon "%ROOT%\src\visor\assets\visor.ico" ^
    --add-data "%ROOT%\src\visor\assets\visor.ico;visor/assets" ^
    --add-data "%ROOT%\src\visor\assets\visor.svg;visor/assets" ^
    --add-data "%ROOT%\src\visor\assets\icons;visor/assets/icons" ^
    "%ROOT%\src\visor\__main__.py"

if errorlevel 1 (
    echo ERROR: PyInstaller build failed.
    pause
    exit /b 1
)

if exist "%ROOT%\dist\VISOR\VISOR.exe" (
    echo =========================================
    echo BUILD SUCCESSFUL
    echo exe = %ROOT%\dist\VISOR\VISOR.exe
    echo =========================================
) else (
    echo =========================================
    echo BUILD FAILED
    echo Expected output was not created.
    echo =========================================
    pause
    exit /b 1
)

pause
