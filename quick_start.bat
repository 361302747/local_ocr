@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
call "%~dp0start.bat"
echo.
echo [INFO] quick_start finished.
pause
