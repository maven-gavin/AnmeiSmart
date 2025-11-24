from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.common.deps.database import Base
from app.common.deps.uuid_utils import generate_uuid


class UUIDMixin:
    """提供UUID主键的Mixin类"""
    id = Column(String(36), primary_key=True, default=generate_uuid)


class TimestampMixin:
    """提供创建和更新时间戳的Mixin类"""
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="创建人ID")
    updated_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="修改人ID")


class BaseModel(Base, UUIDMixin, TimestampMixin):
    """基础模型类，提供UUID主键和时间戳
    
    所有模型都应该继承这个类，而不是直接继承 Base
    """
    __abstract__ = True  # 标记为抽象类，不会创建数据库表 