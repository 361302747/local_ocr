@echo off
chcp 65001 >nul 2>&1
setlocal
cd /d "%~dp0"

set "PYTHON_EXE="
set "PYTHON_ARGS="
if defined LOCAL_OCR_PYTHON set "PYTHON_EXE=%LOCAL_OCR_PYTHON%"
if not defined PYTHON_EXE (
    if exist "%~dp0.venv\Scripts\python.exe" set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
)
if not defined PYTHON_EXE (
    py -3.11 --version >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=py"
        set "PYTHON_ARGS=-3.11"
    )
)
if not defined PYTHON_EXE set "PYTHON_EXE=python"
"%PYTHON_EXE%" %PYTHON_ARGS% -c "import sys; sys.exit(0 if sys.version_info[:2] == (3, 11) else 1)"
if errorlevel 1 (
    echo [ERROR] This bytecode package requires Python 3.11.
    set "EXIT_CODE=1"
    goto :finish
)

echo [INFO] Installing Local OCR dependencies...
"%PYTHON_EXE%" %PYTHON_ARGS% -m pip install -r "%~dp0requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo [ERROR] Dependency installation failed.
    set "EXIT_CODE=1"
    goto :finish
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_easyocr_models.ps1"
set "EXIT_CODE=%ERRORLEVEL%"

:finish
echo [INFO] Installer finished with exit code %EXIT_CODE%.
pause
exit /b %EXIT_CODE%
