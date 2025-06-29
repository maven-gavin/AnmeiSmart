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
    MONGODB_ENABLED: bool = True
    
    # Redis配置
    REDIS_URL: str = "redis://:difyai123456@localhost:6379"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "difyai123456"
    REDIS_DB: int = 0
    
    # Minio配置
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_BUCKET_NAME: str = "chat-files"
    
    # JWT配置
    SECRET_KEY: str = "difyai123456"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # AI服务配置
    AI_API_KEY: str = "your_ai_api_key"
    AI_MODEL: str = "default"
    AI_API_BASE_URL: str = "https://api.example.com"
    
    # OpenAI配置
    OPENAI_API_KEY: str = "your_openai_api_key"
    OPENAI_API_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    
    # 通知服务配置
    NOTIFICATION_PROVIDER: str = "logging"  # logging, firebase, apns
    
    # Firebase配置 (TODO: 待实现)
    FIREBASE_CREDENTIALS_PATH: str = ""
    FIREBASE_PROJECT_ID: str = ""
    
    # Apple Push Notification配置 (TODO: 待实现)
    APNS_KEY_PATH: str = ""
    APNS_KEY_ID: str = ""
    APNS_TEAM_ID: str = ""
    APNS_BUNDLE_ID: str = ""
    
    model_config = ConfigDict(case_sensitive=True, env_file=".env", extra="ignore")

@lru_cache()
def get_settings() -> Settings:
    """获取应用配置单例"""
    return Settings() 