from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI智能助手系统"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Google AI Studio API配置
    GOOGLE_AI_API_KEY: str = os.getenv("GOOGLE_AI_API_KEY", "")
    
    # 文件上传配置
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    
    # 支持的文件类型
    ALLOWED_PDF_TYPES: list = ["application/pdf"]
    ALLOWED_AUDIO_TYPES: list = ["audio/wav", "audio/mp3", "audio/m4a"]
    ALLOWED_VIDEO_TYPES: list = ["video/mp4", "video/avi", "video/quicktime"]
    
    class Config:
        case_sensitive = True

settings = Settings() 