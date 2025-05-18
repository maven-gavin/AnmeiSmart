from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.orm.session import Session
from sqlalchemy.pool import NullPool
from typing import Generator, Any
import importlib.util
import sys
import logging

from app.core.config import get_settings

settings = get_settings()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# PostgreSQL或其他数据库配置
engine = create_engine(
    settings.DATABASE_URL, 
    poolclass=NullPool
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

# 依赖注入函数，用于提供数据库会话
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 使用同步会话执行数据库操作的帮助函数
def with_db(func):
    """装饰器，提供数据库会话给被装饰的函数"""
    def wrapper(*args, **kwargs):
        db = SessionLocal()
        try:
            result = func(db, *args, **kwargs)
            return result
        finally:
            db.close()
    return wrapper

# 初始化数据库
def init_db():
    # 在这里导入模型，避免循环导入
    from app.db.models.user import User, Role
    from app.db.models.chat import Conversation, Message, CustomerProfile
    from app.db.models.system import SystemSettings, AIModelConfig
    Base.metadata.create_all(bind=engine)

# 创建初始角色
@with_db
def create_initial_roles(db: Session):
    from app.db.models.user import Role
    
    # 角色列表
    roles = [
        {"name": "admin", "description": "系统管理员"},
        {"name": "customer", "description": "顾客"},
        {"name": "consultant", "description": "医美顾问"},
        {"name": "doctor", "description": "医生"},
        {"name": "operator", "description": "运营人员"}
    ]
    
    # 检查并创建角色
    for role_data in roles:
        role = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not role:
            role = Role(**role_data)
            db.add(role)
    
    db.commit()

# 创建初始系统设置
@with_db
def create_initial_system_settings(db: Session):
    from app.db.models.system import SystemSettings, AIModelConfig
    
    # 检查是否已存在系统设置
    system_settings = db.query(SystemSettings).first()
    if not system_settings:
        # 创建默认系统设置
        system_settings = SystemSettings(
            siteName="安美智能咨询系统",
            logoUrl="/logo.png",
            themeColor="#FF6B00",
            defaultModelId="GPT-4",
            maintenanceMode=False,
            userRegistrationEnabled=True
        )
        db.add(system_settings)
        db.commit()
        db.refresh(system_settings)
        
        # 创建默认AI模型配置
        default_model = AIModelConfig(
            modelName="GPT-4",
            apiKey="sk-••••••••••••••••••••••••",  # 实际部署时应使用环境变量或安全存储
            baseUrl="https://api.openai.com/v1",
            maxTokens=2000,
            temperature=0.7,
            enabled=True,
            system_settings_id=system_settings.id
        )
        db.add(default_model)
        db.commit()
        
        logger.info("初始系统设置已创建")
    
    return system_settings

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

# MongoDB连接管理
def get_mongodb() -> Any:
    return mongodb

# Weaviate连接管理
def get_weaviate() -> Any:
    return weaviate_client 