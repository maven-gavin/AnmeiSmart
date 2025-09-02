from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.orm.session import Session
from sqlalchemy.pool import NullPool
from typing import Generator, Any, Callable, TypeVar
import importlib.util
import logging
from functools import wraps

F = TypeVar('F', bound=Callable[..., Any])

from app.core.config import get_settings

settings = get_settings()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# PostgreSQL或其他数据库配置
engine = create_engine(
    settings.DATABASE_URL, 
    poolclass=NullPool,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
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
def with_db(func: F) -> F:
    """装饰器，提供数据库会话给被装饰的函数"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        db = SessionLocal()
        try:
            result = func(db=db, *args, **kwargs)
            return result
        finally:
            db.close()
    return wrapper  # type: ignore

# 初始化数据库
def init_db():
    # 导入所有数据库模型，确保SQLAlchemy可以正确建立关系映射
    # 显式导入所有模型以避免linter警告
    from app.common.infrastructure.db.models import (
        BaseModel, User, Role, Doctor, Consultant, Operator, Administrator,
        UserPreferences, UserDefaultRole, LoginHistory, Customer, CustomerProfile,
        SystemSettings, Conversation, Message, MessageAttachment, 
        PlanGenerationSession, PlanDraft, InfoCompleteness, DigitalHuman,
        ContactTag, ContactGroup, ContactPrivacySetting, Friendship, PendingTask, MCPToolGroup,
        MCPTool, MCPCallLog, AgentConfig, UploadSession, UploadChunk
    )
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)

# 创建初始角色
@with_db
def create_initial_roles(db: Session):
    from app.identity_access.infrastructure.db.user import Role
    from app.common.infrastructure.db.uuid_utils import role_id
    
    # 角色列表
    roles = ["customer", "consultant", "doctor", "operator", "admin"]
    
    # 检查并创建角色
    for role_name in roles:
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            role = Role(id=role_id(), name=role_name)
            db.add(role)
    
    db.commit()
    logger.info("初始角色已创建")

# 创建初始系统设置
@with_db
def create_initial_system_settings(db: Session):
    from app.system.infrastructure.db.system import SystemSettings
    from app.common.infrastructure.db.uuid_utils import system_id
    
    # 检查是否已存在系统设置
    system_settings = db.query(SystemSettings).first()
    if not system_settings:
        # 创建默认系统设置
        settings_id = system_id()
        system_settings = SystemSettings(
            id=settings_id,
            siteName="安美智能咨询系统",
            logoUrl="/logo.png",
            defaultModelId="GPT-4",
            maintenanceMode=False,
            userRegistrationEnabled=True
        )
        db.add(system_settings)
        db.commit()
        db.refresh(system_settings)
        

        
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

# MongoDB连接管理
def get_mongodb() -> Any:
    return mongodb 