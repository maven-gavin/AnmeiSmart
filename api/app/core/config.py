from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """应用配置类"""
    PROJECT_NAME: str = "安美智享智能医美服务系统"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS配置
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # Next.js frontend
        "http://localhost:8000",  # FastAPI Swagger UI
    ]
    
    # 数据库配置
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/dbname"
    MONGODB_URL: str = "mongodb://localhost:27017"
    WEAVIATE_URL: str = "http://localhost:8080"
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        case_sensitive = True
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    """获取应用配置单例"""
    return Settings() 