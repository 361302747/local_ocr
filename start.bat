@echo off
chcp 65001 >nul 2>&1
setlocal
cd /d "%~dp0"

set "OLLAMA_HOST=127.0.0.1:11434"
set "OLLAMA_BASE_URL=http://127.0.0.1:11434"
set "OCR_MODEL=glm-ocr"

set "HOST=127.0.0.1"
set "PORT=8765"
set "OCR_ENGINE=none"
set "LMSTUDIO_API_URL=%OLLAMA_BASE_URL%/api/generate"
set "LMSTUDIO_MODEL=%OCR_MODEL%"
set "LMSTUDIO_TIMEOUT=120"
set "VLM_API_MODE=ollama"

echo ====================================
echo Local OCR Service Starting...
echo ====================================
echo.

where ollama >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Ollama was not found.
    echo [INFO] Install it first:
    echo        https://ollama.com/download/windows
    pause
    exit /b 1
)

echo [INFO] Checking Ollama service on %OLLAMA_BASE_URL% ...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ok=$false; try { Invoke-RestMethod '%OLLAMA_BASE_URL%/api/tags' -TimeoutSec 2 | Out-Null; $ok=$true } catch {}; if (-not $ok) { exit 1 }"
if errorlevel 1 (
    echo [INFO] Starting Ollama service...
    start "Ollama" /min ollama serve
)

echo [INFO] Waiting for Ollama service...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$deadline=(Get-Date).AddSeconds(30); while((Get-Date) -lt $deadline) { try { Invoke-RestMethod '%OLLAMA_BASE_URL%/api/tags' -TimeoutSec 2 | Out-Null; exit 0 } catch { Start-Sleep -Seconds 1 } }; exit 1"
if errorlevel 1 (
    echo [ERROR] Ollama service did not become ready.
    pause
    exit /b 1
)

echo [INFO] Checking model: %OCR_MODEL%
ollama list | findstr /i /c:"%OCR_MODEL%" >nul 2>nul
if errorlevel 1 (
    echo [INFO] Pulling model %OCR_MODEL% ...
    ollama pull %OCR_MODEL%
    if errorlevel 1 (
        echo [ERROR] Failed to pull %OCR_MODEL%.
        pause
        exit /b 1
    )
)

echo.
echo [INFO] Ollama:   %OLLAMA_BASE_URL%
echo [INFO] Model:    %OCR_MODEL%
echo [INFO] LocalOCR: http://127.0.0.1:%PORT%
echo [INFO] API Docs: http://127.0.0.1:%PORT%/docs
echo.

uv run python main.py

pause
