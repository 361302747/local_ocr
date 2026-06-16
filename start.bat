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
set "LMSTUDIO_TIMEOUT=120"
set "VLM_API_MODE=openai"
set "VLM_MAX_TOKENS=512"

echo ====================================
echo Local OCR Service Starting...
echo Backend: LM Studio
echo ====================================
echo.

echo [INFO] Checking LM Studio local server on %LMSTUDIO_BASE_URL% ...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "try { Invoke-RestMethod '%LMSTUDIO_BASE_URL%/v1/models' -TimeoutSec 3 | Out-Null; exit 0 } catch { exit 1 }"
if errorlevel 1 (
    echo [ERROR] LM Studio local server is not available.
    echo [INFO] Please open LM Studio, load the GLM-OCR model, and start Local Server.
    echo [INFO] Expected endpoint: %LMSTUDIO_API_URL%
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

uv run python main.py
set "EXIT_CODE=%ERRORLEVEL%"

:finish
echo.
if "%EXIT_CODE%"=="" set "EXIT_CODE=0"
echo [INFO] Script finished with exit code %EXIT_CODE%.
pause
exit /b %EXIT_CODE%
