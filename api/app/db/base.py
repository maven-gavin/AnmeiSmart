from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
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

# Weaviate配置 - 使用v3客户端API (兼容Weaviate 1.19.0)
try:
    # 使用v3客户端API连接Weaviate
    weaviate_auth_config = weaviate.AuthApiKey(api_key=settings.WEAVIATE_API_KEY) if settings.WEAVIATE_API_KEY else None
    weaviate_client = weaviate.Client(
        url=settings.WEAVIATE_URL,
        auth_client_secret=weaviate_auth_config
    )
    # 测试连接
    try:
        weaviate_client.schema.get()
        print(f"Weaviate连接成功")
    except Exception as e:
        print(f"Weaviate连接警告: {str(e)}")
except Exception as e:
    print(f"Weaviate连接错误: {str(e)}")
    # 创建一个空的客户端对象，允许应用程序继续运行
    # 这样即使Weaviate不可用，应用程序的其他部分仍然可以工作
    weaviate_client = None

# 数据库会话管理
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# MongoDB连接管理
def get_mongodb() -> Any:
    return mongodb

# Weaviate连接管理
def get_weaviate() -> Any:
    return weaviate_client 