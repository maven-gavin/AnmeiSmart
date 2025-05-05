from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from motor.motor_asyncio import AsyncIOMotorClient
import weaviate
from typing import Generator, Any

from app.core.config import get_settings

settings = get_settings()

# PostgreSQL配置
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# MongoDB配置
mongodb_client = AsyncIOMotorClient(settings.MONGODB_URL)
mongodb = mongodb_client.medical_beauty

# Weaviate配置
weaviate_client = weaviate.Client(settings.WEAVIATE_URL)

def get_db() -> Generator[Any, None, None]:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_mongodb() -> AsyncIOMotorClient:
    """获取MongoDB客户端"""
    return mongodb

def get_weaviate() -> weaviate.Client:
    """获取Weaviate客户端"""
    return weaviate_client 