"""
OCR服务配置文件
"""
from pydantic_settings import BaseSettings
from typing import Optional, List
from pathlib import Path


class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8765
    
    ocr_engine: str = "easyocr"
    ocr_languages: List[str] = ["ch_sim"]
    ocr_use_gpu: bool = True
    ocr_charset_file: str = "resource/common_ch_sim_clean.txt"
    
    lmstudio_api_url: str = "http://localhost:1234/v1/chat/completions"
    lmstudio_model: str = "glm-ocr"
    lmstudio_timeout: int = 60
    
    tesseract_cmd: Optional[str] = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


PROJECT_ROOT = Path(__file__).parent


settings = Settings()
