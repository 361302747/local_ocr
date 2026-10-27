# Local OCR

基于 FastAPI 的 OCR 服务，支持 LM Studio GLM-OCR 和按需加载的 EasyOCR。

开发机运行 `start.bat` 时自动准备本机 LM Studio、加载已下载的 `glm-ocr` 并验证 API。
开发启动脚本使用 `E:\python\ghost_catcher\.venv\Scripts\python.exe`；其他机器需修改该解释器路径或使用分发包。

## 分发包

使用 Python 3.11 编译业务模块为 `.pyc`，放入独立 `runtime` 目录，压缩包不包含 `.py` 或本地 `.env`。
运行端同样需要 Python 3.11、OCR 依赖以及已下载 GLM-OCR 的 LM Studio。

```powershell
.\build_distribution.ps1 -PythonExe 'E:\python\ghost_catcher\.venv\Scripts\python.exe' -DistributionRoot 'E:\python\local_ocr_dist'
```

打包前在 `<DistributionRoot>\local_ocr\resource\` 准备 `common_ch_sim_clean.txt` 和
`easyocr\model\craft_mlt_25k.pth`、`easyocr\model\zh_sim_g2.pth`。
EasyOCR 模型不纳入 Git，打包时从本地分发资源读取。
每次仅生成并覆盖 `local_ocr_ready.zip`，其他历史压缩包不自动删除。

用户关闭旧服务，覆盖解压后运行 `start.bat` 或 `quick_start.bat`；已有 `.env` 保留。
详见 `packaging/README_START.txt`。

## 验证

使用项目 Python 3.11 环境执行启动逻辑测试（进程超时 30 秒）：

```powershell
& E:\python\ghost_catcher\.venv\Scripts\python.exe -c 'import subprocess,sys; sys.exit(subprocess.run([sys.executable,"-m","unittest","discover","-s","test_script/tools","-p","test_ensure_lmstudio.py","-v"],timeout=30).returncode)'
```
