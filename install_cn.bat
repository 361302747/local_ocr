@echo off
chcp 65001 >nul 2>&1
setlocal
cd /d "%~dp0"

set "PYTHON=python"
set "PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple"
set "PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn"
set "TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu"

echo ====================================
echo local_ocr 国内镜像安装脚本
echo ====================================
echo [INFO] 工作目录: %CD%
echo [INFO] PyPI 镜像: %PIP_INDEX_URL%
echo [INFO] PyTorch 源: %TORCH_INDEX_URL%
echo.

where %PYTHON% >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 未找到 python，请先安装 Python 3.10+ 并加入 PATH
    set "EXIT_CODE=1"
    goto :finish
)

echo [INFO] Python 版本:
%PYTHON% --version
if errorlevel 1 (
    echo [ERROR] Python 无法正常运行
    set "EXIT_CODE=1"
    goto :finish
)

echo.
echo [STEP] 升级 pip / setuptools / wheel
%PYTHON% -m pip install -U pip setuptools wheel -i %PIP_INDEX_URL% --trusted-host %PIP_TRUSTED_HOST%
if errorlevel 1 (
    echo [ERROR] 基础打包工具升级失败
    set "EXIT_CODE=1"
    goto :finish
)

echo.
echo [STEP] 安装 PyTorch CPU 版本
%PYTHON% -m pip install -U torch torchvision --index-url %TORCH_INDEX_URL%
if errorlevel 1 (
    echo [ERROR] PyTorch 安装失败
    set "EXIT_CODE=1"
    goto :finish
)

echo.
echo [STEP] 安装 local_ocr requirements
%PYTHON% -m pip install -r requirements.txt -i %PIP_INDEX_URL% --trusted-host %PIP_TRUSTED_HOST%
if errorlevel 1 (
    echo [ERROR] requirements 安装失败
    set "EXIT_CODE=1"
    goto :finish
)

echo.
echo [STEP] 校验关键依赖
%PYTHON% -c "import fastapi, uvicorn, cv2, easyocr, torch; print('fastapi ok'); print('uvicorn ok'); print('cv2 ok'); print('easyocr ok'); print('torch ok')"
if errorlevel 1 (
    echo [ERROR] 依赖校验失败
    set "EXIT_CODE=1"
    goto :finish
)

echo.
echo [SUCCESS] 安装完成，可以运行 start.bat 启动服务
set "EXIT_CODE=0"

:finish
echo.
pause
exit /b %EXIT_CODE%
