@echo off
chcp 65001 >nul 2>&1
setlocal
cd /d "%~dp0"

set "HOST=0.0.0.0"
set "PORT=8765"
set "OCR_ENGINE=none"
set "LMSTUDIO_BASE_URL=http://127.0.0.1:1234"
set "LMSTUDIO_API_URL=%LMSTUDIO_BASE_URL%/v1/chat/completions"
set "LMSTUDIO_MODEL=glm-ocr"
set "LMSTUDIO_MODEL_KEY=glm-ocr"
set "LMSTUDIO_LOAD_TIMEOUT=180"
set "LMSTUDIO_TIMEOUT=120"
set "VLM_API_MODE=openai"
set "VLM_MAX_TOKENS=512"

echo ====================================
echo Local OCR Service Starting...
echo Backend: LM Studio
echo ====================================
echo.

set "PYTHON="
if defined LOCAL_OCR_PYTHON set "PYTHON=%LOCAL_OCR_PYTHON%"
if not defined PYTHON (
    if exist "E:\python\ghost_catcher\.venv\Scripts\python.exe" set "PYTHON=E:\python\ghost_catcher\.venv\Scripts\python.exe"
)
if not defined PYTHON set "PYTHON=python"
"%PYTHON%" --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is unavailable: %PYTHON%
    echo [INFO] Add Python to PATH or set LOCAL_OCR_PYTHON to python.exe.
    set "EXIT_CODE=1"
    goto :finish
)

echo [INFO] Python: %PYTHON%
echo [INFO] Preparing LM Studio and model %LMSTUDIO_MODEL% ...
"%PYTHON%" "%~dp0ensure_lmstudio.py"
if errorlevel 1 (
    echo [ERROR] Could not prepare LM Studio. See the error above.
    set "EXIT_CODE=1"
    goto :finish
)

echo [INFO] LM Studio local server is available.

echo.
echo [INFO] Backend:  %LMSTUDIO_BASE_URL%
echo [INFO] Model:    %LMSTUDIO_MODEL%
echo [INFO] LocalOCR: http://%COMPUTERNAME%:%PORT%
echo [INFO] API Docs: http://%COMPUTERNAME%:%PORT%/docs
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "if (Get-NetTCPConnection -LocalPort %PORT% -State Listen -ErrorAction SilentlyContinue) { exit 0 }; exit 1"
if not errorlevel 1 (
    echo [INFO] local_ocr is already running on port %PORT%.
    set "EXIT_CODE=0"
    goto :finish
)

"%PYTHON%" main.py
set "EXIT_CODE=%ERRORLEVEL%"

:finish
echo.
if "%EXIT_CODE%"=="" set "EXIT_CODE=0"
echo [INFO] Script finished with exit code %EXIT_CODE%.
pause
exit /b %EXIT_CODE%
