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
if not defined PYTHON_EXE (
    python --version >nul 2>&1
    if not errorlevel 1 set "PYTHON_EXE=python"
)
if not defined PYTHON_EXE (
    echo [ERROR] Python not found. Install Python 3.11 and retry.
    set "EXIT_CODE=1"
    goto :finish
)

"%PYTHON_EXE%" %PYTHON_ARGS% -c "import sys; sys.exit(0 if sys.version_info[:2] == (3, 11) else 1)"
if errorlevel 1 (
    echo [ERROR] This bytecode package requires Python 3.11.
    set "EXIT_CODE=1"
    goto :finish
)

if not exist "%~dp0.env" (
    if exist "%~dp0.env.example" copy "%~dp0.env.example" "%~dp0.env" >nul
)

echo ====================================
echo Local OCR Service Starting...
echo ====================================
echo [INFO] Python: %PYTHON_EXE% %PYTHON_ARGS%

"%PYTHON_EXE%" %PYTHON_ARGS% -c "import fastapi, uvicorn, pydantic_settings, httpx, cv2, numpy" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing Python dependencies...
    "%PYTHON_EXE%" %PYTHON_ARGS% -m pip install -r "%~dp0requirements.txt"
    if errorlevel 1 (
        echo [ERROR] Dependency installation failed. Try install_deps.bat.
        set "EXIT_CODE=1"
        goto :finish
    )
)

echo [INFO] Installing packaged EasyOCR models...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_easyocr_models.ps1"
if errorlevel 1 (
    echo [ERROR] EasyOCR model installation failed.
    set "EXIT_CODE=1"
    goto :finish
)

echo [INFO] Preparing LM Studio and the configured model...
"%PYTHON_EXE%" %PYTHON_ARGS% "%~dp0runtime\ensure_lmstudio.pyc"
if errorlevel 1 (
    echo [ERROR] LM Studio startup failed. See the error above.
    set "EXIT_CODE=1"
    goto :finish
)

"%PYTHON_EXE%" %PYTHON_ARGS% "%~dp0runtime\main.pyc"
set "EXIT_CODE=%ERRORLEVEL%"

:finish
if not defined EXIT_CODE set "EXIT_CODE=0"
echo [INFO] Script finished with exit code %EXIT_CODE%.
pause
exit /b %EXIT_CODE%
