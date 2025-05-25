from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache
from pydantic import ConfigDict

class Settings(BaseSettings):
    """应用配置类"""
    PROJECT_NAME: str = "安美智享智能医美服务系统"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS配置
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # Next.js frontend
        "http://localhost:8000",  # FastAPI Swagger UI
        "http://127.0.0.1:3000",  # Next.js on localhost IP
        "http://127.0.0.1:8000",  # FastAPI on localhost IP
        "http://169.254.89.234:3000",  # Remote access IP (shown in terminal)
    ]
    
    # 数据库配置
    DATABASE_URL: str = "postgresql://postgres:difyai123456@localhost:5432/anmeismart"
    MONGODB_URL: str = "mongodb://localhost:27017"
    WEAVIATE_URL: str = "http://localhost:8080"
    WEAVIATE_API_KEY: str = "WVF5YThaHlkYwhGUSmCRgsX3tD5ngdN8pkih"
    MONGODB_ENABLED: bool = True
    
    # JWT配置
    SECRET_KEY: str = "difyai123456"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # AI服务配置
    AI_API_KEY: str = "your_ai_api_key"
    AI_MODEL: str = "default"
    AI_API_BASE_URL: str = "https://api.example.com"
    
    # OpenAI配置
    OPENAI_API_KEY: str = "your_openai_api_key"
    OPENAI_API_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    
    model_config = ConfigDict(case_sensitive=True, env_file=".env")

@lru_cache()
def get_settings() -> Settings:
    """获取应用配置单例"""
    return Settings() 