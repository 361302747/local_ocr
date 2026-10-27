OCR 服务更新包（2026-10-28）

更新方式：
1. 关闭正在运行的旧 OCR 服务。
2. 将压缩包中的 local_ocr 文件夹内容覆盖到原服务目录。
3. 双击 start.bat 或 quick_start.bat。

压缩包不包含 .env，覆盖更新会保留原配置；首次使用会从 .env.example 创建配置。
Python 业务模块以 runtime 目录中的 .pyc 分发，不包含 .py 源文件。
旧目录残留的 .py 不会被新启动入口导入，可在确认不再需要后自行清理。
必须使用 Python 3.11；已有 .venv 若为其他版本，需要重新建立 3.11 环境并安装依赖。
同为 Python 3.11 且依赖完整时，无需重新安装。

自动加载条件：
- 已安装 Python 3.11 和 OCR 依赖（缺失依赖时启动脚本会尝试安装）。
- 已安装支持 lms daemon / load 命令的 LM Studio。
- lms 已加入 PATH，或位于当前用户的 .lmstudio\bin\lms.exe。
- 已在 LM Studio 下载 GLM-OCR，模型 key 为 glm-ocr。
- 使用本机 LM Studio；默认地址 http://127.0.0.1:1234。

启动脚本自动准备后台运行时、加载配置的模型、启动 API 并检查就绪状态。
已加载的模型直接复用；默认模型加载超时 180 秒。失败时停止启动 OCR 并显示原因。
不需要手动打开 LM Studio 界面或点击加载模型。
模型加载后保持驻留，退出 OCR 不会自动卸载模型或关闭 LM Studio。
本包包含 EasyOCR 离线模型，不包含 LM Studio 安装程序、GLM-OCR 模型或 Python。

服务默认端口 8765；浏览器打开 http://127.0.0.1:8765/docs。
配置修改请编辑 .env；其他后端或远程地址跳过本机自动启动。
仅双击 start.bat / quick_start.bat 会自动准备 LM Studio，直接运行 runtime/main.pyc 不会。
