from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.orm.session import Session
from sqlalchemy.pool import NullPool
from typing import Generator, Callable, TypeVar, Any
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
    """初始化数据库，通过导入各领域模型确保映射完整"""
    # 导入各领域的模型初始化文件，确保SQLAlchemy可以正确建立关系映射
    # import app.identity_access.infrastructure.db # 已迁移到models
    import app.identity_access.models.user
    import app.identity_access.models.profile
    import app.digital_humans.models  # Move up before chat
    import app.chat.models
    import app.contacts.models
    import app.tasks.models
    import app.mcp.models
    # AI模块模型已迁移到新架构，不再需要单独导入
    import app.system.models
    import app.customer.models
    import app.common.models.upload
    import app.common.models.file
    import app.channels.models  # 渠道模型
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    logger.info("数据库表创建完成")

# 创建初始角色
@with_db
def create_initial_roles(db: Session):
    from app.identity_access.models.user import Role
    from app.common.deps.uuid_utils import role_id
    
    # 角色列表
    roles = ["customer", "operator", "administrator"]
    
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
    from app.system.models.system import SystemSettings
    from app.common.deps.uuid_utils import system_id
    
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
