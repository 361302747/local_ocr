# Local OCR

基于 FastAPI 的 OCR 服务，支持 LM Studio GLM-OCR 和启动时预加载的 EasyOCR。

OCR 服务访问 LM Studio／Ollama 的识别与健康检查接口时使用直连，忽略环境代理；启动阶段的 LM Studio API 探测同样不使用代理。

默认 `OCR_ENGINE=easyocr`，在应用启动阶段加载 EasyOCR，初始化完成后再开始接收请求，避免首次 `/ocr` 请求因加载模型而超过客户端的 2 秒时限。`start.bat` 同样显式启用预加载；直接启动时环境变量或 `.env` 可覆盖默认值。修改后需关闭旧 OCR 服务，再重新运行启动脚本；脚本检测到服务已运行时不会替换它。

开发机运行 `start.bat` 时自动准备本机 LM Studio、加载已下载的 `glm-ocr` 并验证 API。
源码启动脚本按以下顺序选择 Python：环境变量 `LOCAL_OCR_PYTHON` → 本机原虚拟环境 `E:\python\ghost_catcher\.venv\Scripts\python.exe`（存在时）→ PATH 中的 `python`。本机无需额外设置，远端没有该虚拟环境时自动使用默认 Python。
可将 `LOCAL_OCR_PYTHON` 设为 `python` 强制使用默认环境，或设为其他 `python.exe` 的完整路径；路径值不要包含额外的引号。显式指定的解释器不可用时直接报错，不自动切换。依赖须安装到实际选中的解释器环境。

```powershell
# 强制使用 PATH 中的 Python（仅当前 PowerShell 会话）
$env:LOCAL_OCR_PYTHON = 'python'
.\start.bat

# 恢复自动选择
Remove-Item Env:LOCAL_OCR_PYTHON -ErrorAction SilentlyContinue
```

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
# 宿主机日常统计与助手信号

订阅本服务的虚拟机只访问 OCR 端口，不直接打开宿主 SQLite。接口只在受信任的宿主机／虚拟机网络内开放，不转发到公网。

1. 停止旧日常／挂机助手和旧独立信号服务。不能同时运行两个信号中心。保留旧进度 JSON。
2. 在宿主机以以后运行 OCR 的同一 Windows 用户，用启动 OCR 的 Python 执行 `activity_progress.py --import-json <旧 activity_daily_progress.json 的绝对路径>`，不需要 OCR 服务已启动。仅在确认无旧统计时使用 `--initialize-empty`；成功后重复导入不会改写统计。精简版入口是 `runtime/activity_progress.pyc`。历史 JSON 不修改；从未写入的数量不会凭空补齐。
3. 启动 OCR 服务。源代码部署默认查找同级 `ghost_catcher`；部署位置不同时，启动前设置环境变量 `GHOST_CATCHER_PROJECT_ROOT` 为宿主机可访问的脚本库路径。若原信号数据库不在该项目的本地 `runtime/signal_service/state.sqlite3`，用 `GHOST_CATCHER_SIGNAL_DATABASE` 指定原数据库的宿主机本地路径。
4. 所有虚拟机使用更新后的脚本，令 `config/service_connections.json` 的 `signal_service.transport` 为 `ocr`，共用 host 和 OCR 端口，然后启动助手。旧的信号端口环境覆盖需清除或改成新端口。重启后在线状态由助手新心跳建立。

日常统计库位于宿主机当前用户的 `%LOCALAPPDATA%\GhostCatcher\activity_progress.sqlite3`，不要放进 SMB 目录。断线时客户端保存待提交记录，恢复后补交，服务端按事件 ID 去重。
