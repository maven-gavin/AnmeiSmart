from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator, Any
import importlib.util
import sys
import logging

from app.core.config import get_settings

settings = get_settings()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# PostgreSQL配置
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# MongoDB配置 - 条件导入
mongodb_client = None
mongodb = None
if settings.MONGODB_URL:
    try:
        if importlib.util.find_spec("motor"):
            from motor.motor_asyncio import AsyncIOMotorClient
            mongodb_client = AsyncIOMotorClient(settings.MONGODB_URL)
            mongodb = mongodb_client.medical_beauty
            logger.info("MongoDB连接成功")
        else:
            logger.warning("未安装MongoDB客户端依赖(motor)，MongoDB功能将不可用")
    except Exception as e:
        logger.error(f"MongoDB连接错误: {str(e)}")

# Weaviate配置 - 条件导入
weaviate_client = None
if settings.WEAVIATE_URL:
    try:
        if importlib.util.find_spec("weaviate"):
            import weaviate
            # 使用v3客户端API连接Weaviate
            weaviate_auth_config = weaviate.AuthApiKey(api_key=settings.WEAVIATE_API_KEY) if settings.WEAVIATE_API_KEY else None
            weaviate_client = weaviate.Client(
                url=settings.WEAVIATE_URL,
                auth_client_secret=weaviate_auth_config
            )
            # 测试连接
            weaviate_client.schema.get()
            logger.info("Weaviate连接成功")
        else:
            logger.warning("未安装Weaviate客户端依赖(weaviate-client)，Weaviate功能将不可用")
    except Exception as e:
        logger.warning(f"Weaviate连接警告: {str(e)}")

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