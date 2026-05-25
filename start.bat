@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo ====================================
echo OCR Service Starting...
echo ====================================
echo.

echo [INFO] Starting OCR Service...
echo [INFO] Local: http://localhost:8765
echo [INFO] LAN: http://192.168.1.2:8765
echo [INFO] API Docs: http://localhost:8765/docs
echo.

uv run python main.py

pause
