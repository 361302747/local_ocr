---
name: "local-ocr-project"
description: "OCR服务项目技能。本项目使用uv管理依赖，提供本地OCR服务和LMStudio OCR接口。启动服务使用 python main.py，服务地址 http://localhost:8765。"
---

# OCR服务项目

## 项目概述

本项目是一个统一的OCR识别服务，支持本地OCR引擎和LMStudio OCR识别。

## 快速启动

### 方式一：双击启动（推荐）
```
双击 start.bat      # 带日志显示
双击 quick_start.bat # 后台启动
```

### 方式二：命令行启动
```bash
# 使用 uv（推荐）
uv run python main.py

# 或直接运行
python main.py
```

## 服务地址

| 访问方式 | 地址 |
|---------|------|
| 本地访问 | http://localhost:8765 |
| 局域网访问 | http://192.168.1.2:8765 |
| API文档 | http://localhost:8765/docs |

## API接口

### 本地OCR识别
- POST /ocr - base64图片识别
- POST /ocr/upload - 文件上传识别

### LMStudio OCR识别
- POST /lmstudio/ocr - base64图片识别
- POST /lmstudio/ocr/upload - 文件上传识别

### 健康检查
- GET /health

## 配置

配置文件：`.env`（复制 `.env.example`）

主要配置项：
- OCR_ENGINE: OCR引擎类型（easyocr/tesseract）
- OCR_USE_GPU: 是否使用GPU
- OCR_CHARSET_FILE: 字符集文件路径
- LMSTUDIO_API_URL: LMStudio API地址
- LMSTUDIO_MODEL: LMStudio模型名称

## 测试

```bash
uv run python test_ocr.py
```
