"""
OCR服务主程序 - 提供HTTP API接口
支持本地OCR引擎和LMStudio OCR识别
"""
import logging
from typing import Optional, List
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import numpy as np

from config import settings, PROJECT_ROOT
from ocr_engine import (
    init_ocr_engine,
    get_ocr_engine,
    base64_to_image,
    recognize_text
)
from lmstudio_client import get_lmstudio_client

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OCR服务",
    description="统一的OCR识别服务，支持本地OCR引擎和LMStudio OCR",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback
    error_msg = str(exc)
    trace = traceback.format_exc()
    logger.error(f"全局异常: {error_msg}\n{trace}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": error_msg, "traceback": trace}
    )


class TextBlock(BaseModel):
    """单个文本块的结构"""
    bbox: List[List[float]]
    text: str
    confidence: float

    class Config:
        json_schema_extra = {
            "example": {
                "bbox": [[10, 20], [100, 20], [100, 50], [10, 50]],
                "text": "识别的文字",
                "confidence": 0.95
            },
            "description": """
bbox: 文本块的边界框坐标，四个点的坐标列表 [左上, 右上, 右下, 左下]
      每个点为 [x, y] 格式，x为水平位置，y为垂直位置
text: 识别出的文本内容
confidence: 识别置信度，范围 0-1，值越高表示越可信
"""
        }


class OCRRequest(BaseModel):
    """OCR请求模型 - base64图片"""
    image_base64: str
    return_details: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                "return_details": True
            },
            "description": """
image_base64: Base64编码的图片数据（支持PNG、JPEG等格式）
return_details: 是否返回详细的文本块信息
  - False: 只返回合并后的完整文本
  - True: 返回每个文本块的详细信息（位置、置信度等）
"""
        }


class OCRResponse(BaseModel):
    """OCR响应模型"""
    success: bool
    text: str = ""
    details: Optional[List[TextBlock]] = None
    engine: str = ""
    error: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "text": "北俱郊外地府 TTT4999",
                "details": [
                    {
                        "bbox": [[10, 20], [100, 20], [100, 50], [10, 50]],
                        "text": "北俱郊外地府",
                        "confidence": 0.91
                    },
                    {
                        "bbox": [[110, 20], [200, 20], [200, 50], [110, 50]],
                        "text": "TTT4999",
                        "confidence": 0.98
                    }
                ],
                "engine": "easyocr",
                "error": None
            },
            "description": """
success: 识别是否成功
text: 合并后的完整文本（所有文本块用空格连接）
details: 文本块详细列表（仅当 return_details=True 时返回）
  - bbox: 边界框坐标 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
  - text: 该文本块的文字
  - confidence: 置信度 (0-1)
engine: 使用的OCR引擎名称
error: 错误信息（仅失败时返回）
"""
        }


class LMStudioRequest(BaseModel):
    """LMStudio OCR请求模型"""
    image_base64: str
    prompt: Optional[str] = "请识别图片中的所有文字内容，只返回识别结果，不要添加任何解释。"
    system_prompt: Optional[str] = "你是一个OCR识别助手，专门识别图片中的文字。请准确识别并返回图片中的所有文字内容。"


class LMStudioResponse(BaseModel):
    """LMStudio OCR响应模型"""
    success: bool
    text: str = ""
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str
    ocr_engine: Optional[str] = None
    ocr_available: bool = False
    lmstudio_available: bool = False


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化OCR引擎"""
    logger.info("=" * 50)
    logger.info("OCR服务启动中...")
    logger.info(f"配置 - 引擎: {settings.ocr_engine}, GPU: {settings.ocr_use_gpu}")
    logger.info(f"配置 - 服务地址: {settings.host}:{settings.port}")
    logger.info(f"配置 - LMStudio API: {settings.lmstudio_api_url}")
    logger.info(f"配置 - 字符集: {settings.ocr_charset_file}")
    logger.info("=" * 50)
    
    try:
        charset_path = str(PROJECT_ROOT / settings.ocr_charset_file) if settings.ocr_charset_file else None
        init_ocr_engine(
            engine_type=settings.ocr_engine,
            languages=settings.ocr_languages,
            use_gpu=settings.ocr_use_gpu,
            tesseract_cmd=settings.tesseract_cmd,
            charset_file=charset_path
        )
        engine = get_ocr_engine()
        if engine and engine.is_available:
            logger.info(f"OCR引擎初始化成功: {engine.current_engine_type}")
        else:
            logger.warning("OCR引擎初始化失败，请检查依赖安装")
    except Exception as e:
        logger.error(f"OCR引擎初始化异常: {e}")


@app.get("/", response_model=dict)
async def root():
    """根路径"""
    return {
        "service": "OCR服务",
        "version": "1.0.0",
        "endpoints": {
            "/health": "健康检查",
            "/ocr": "本地OCR识别（POST base64图片）",
            "/ocr/upload": "本地OCR识别（POST上传文件）",
            "/lmstudio/ocr": "LMStudio OCR识别（POST base64图片）",
            "/lmstudio/ocr/upload": "LMStudio OCR识别（POST上传文件）"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    engine = get_ocr_engine()
    lmstudio_client = get_lmstudio_client()
    
    lmstudio_available = await lmstudio_client.health_check()
    
    return HealthResponse(
        status="ok",
        ocr_engine=engine.current_engine_type if engine else None,
        ocr_available=engine.is_available if engine else False,
        lmstudio_available=lmstudio_available
    )


@app.post("/ocr", response_model=OCRResponse, 
         summary="本地OCR识别",
         description="""
## 本地OCR识别接口

使用本地OCR引擎（EasyOCR/Tesseract）识别图片中的文字。

### 请求参数
- `image_base64`: Base64编码的图片数据
- `return_details`: 是否返回详细的文本块信息

### 响应结构

当 `return_details=False` 时：
```json
{
  "success": true,
  "text": "识别出的完整文本",
  "engine": "easyocr"
}
```

当 `return_details=True` 时：
```json
{
  "success": true,
  "text": "识别出的完整文本",
  "details": [
    {
      "bbox": [[x1,y1], [x2,y2], [x3,y3], [x4,y4]],
      "text": "单个文本块内容",
      "confidence": 0.95
    }
  ],
  "engine": "easyocr"
}
```

### 文本块结构说明
- `bbox`: 边界框坐标，四个点 [左上, 右上, 右下, 左下]，每个点为 [x, y]
- `text`: 该文本块识别出的文字
- `confidence`: 置信度 (0-1)，越高越可信
""")
async def ocr_recognize(request: OCRRequest):
    try:
        image = base64_to_image(request.image_base64)
        if image is None:
            raise HTTPException(status_code=400, detail="无效的图片数据")
        
        engine = get_ocr_engine()
        if not engine or not engine.is_available:
            raise HTTPException(status_code=503, detail="OCR引擎不可用")
        
        result = recognize_text(image, request.return_details)
        
        if request.return_details:
            def convert_to_serializable(obj):
                if isinstance(obj, np.ndarray):
                    return [convert_to_serializable(x) for x in obj.tolist()]
                elif isinstance(obj, (np.integer,)):
                    return int(obj)
                elif isinstance(obj, (np.floating,)):
                    return float(obj)
                elif isinstance(obj, list):
                    return [convert_to_serializable(x) for x in obj]
                elif isinstance(obj, tuple):
                    return [convert_to_serializable(x) for x in obj]
                return obj
            
            details = []
            for item in result:
                details.append({
                    "bbox": convert_to_serializable(item[0]),
                    "text": str(item[1]),
                    "confidence": float(item[2])
                })
            
            return OCRResponse(
                success=True,
                text=' '.join([str(item[1]) for item in result]) if result else "",
                details=details,
                engine=engine.current_engine_type
            )
        else:
            return OCRResponse(
                success=True,
                text=result,
                engine=engine.current_engine_type
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR识别失败: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        return OCRResponse(
            success=False,
            error=str(e)
        )


@app.post("/ocr/upload", response_model=OCRResponse,
         summary="本地OCR识别（上传文件）",
         description="""
## 本地OCR识别接口 - 文件上传方式

使用本地OCR引擎识别上传图片中的文字。

### 请求参数
- `file`: 上传的图片文件
- `return_details`: 是否返回详细的文本块信息

### 响应结构
与 `/ocr` 接口相同，详见该接口文档。
""")
async def ocr_recognize_upload(
    file: UploadFile = File(...),
    return_details: bool = Form(False)
):
    try:
        contents = await file.read()
        import base64
        image_base64 = base64.b64encode(contents).decode('utf-8')
        
        return await ocr_recognize(OCRRequest(
            image_base64=image_base64,
            return_details=return_details
        ))
    
    except Exception as e:
        logger.error(f"OCR识别失败: {e}")
        return OCRResponse(
            success=False,
            error=str(e)
        )


@app.post("/lmstudio/ocr", response_model=LMStudioResponse)
async def lmstudio_ocr_recognize(request: LMStudioRequest):
    """
    LMStudio OCR识别 - base64图片
    
    Args:
        request: LMStudio请求，包含base64编码的图片和可选的提示词
    
    Returns:
        LMStudio OCR识别结果
    """
    try:
        client = get_lmstudio_client()
        
        result = await client.recognize_image(
            image_base64=request.image_base64,
            prompt=request.prompt,
            system_prompt=request.system_prompt
        )
        
        return LMStudioResponse(
            success=result["success"],
            text=result["text"],
            error=result.get("error")
        )
    
    except Exception as e:
        logger.error(f"LMStudio OCR识别失败: {e}")
        return LMStudioResponse(
            success=False,
            error=str(e)
        )


@app.post("/lmstudio/ocr/upload", response_model=LMStudioResponse)
async def lmstudio_ocr_recognize_upload(
    file: UploadFile = File(...),
    prompt: Optional[str] = Form("请识别图片中的所有文字内容，只返回识别结果，不要添加任何解释。"),
    system_prompt: Optional[str] = Form("你是一个OCR识别助手，专门识别图片中的文字。请准确识别并返回图片中的所有文字内容。")
):
    """
    LMStudio OCR识别 - 上传文件
    
    Args:
        file: 上传的图片文件
        prompt: 自定义提示词
        system_prompt: 系统提示词
    
    Returns:
        LMStudio OCR识别结果
    """
    try:
        contents = await file.read()
        import base64
        image_base64 = base64.b64encode(contents).decode('utf-8')
        
        return await lmstudio_ocr_recognize(LMStudioRequest(
            image_base64=image_base64,
            prompt=prompt,
            system_prompt=system_prompt
        ))
    
    except Exception as e:
        logger.error(f"LMStudio OCR识别失败: {e}")
        return LMStudioResponse(
            success=False,
            error=str(e)
        )


@app.post("/lmstudio/ocr/custom", response_model=LMStudioResponse)
async def lmstudio_ocr_custom(
    request: LMStudioRequest
):
    """
    LMStudio OCR识别 - 自定义提示词
    
    Args:
        request: LMStudio请求，包含base64编码的图片和自定义提示词
    
    Returns:
        LMStudio OCR识别结果
    """
    return await lmstudio_ocr_recognize(request)


def main():
    """启动服务"""
    logger.info("=" * 50)
    logger.info(f"OCR服务启动中...")
    logger.info(f"Local: http://localhost:{settings.port}")
    logger.info(f"API Docs: http://localhost:{settings.port}/docs")
    logger.info("=" * 50)
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()
