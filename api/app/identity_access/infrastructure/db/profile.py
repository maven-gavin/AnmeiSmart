from sqlalchemy import Boolean, Column, String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.common.infrastructure.db.base_model import BaseModel
from app.common.infrastructure.db.uuid_utils import generate_uuid


class UserPreferences(BaseModel):
    """用户偏好设置表，存储用户个性化配置"""
    __tablename__ = "user_preferences"
    __table_args__ = {"comment": "用户偏好设置表，存储用户个性化配置"}

    id = Column(
        String(36), 
        primary_key=True, 
        default=generate_uuid, 
        comment="偏好设置ID"
    )
    user_id = Column(
        String(36), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False,
        unique=True,
        comment="用户ID"
    )
    notification_enabled = Column(
        Boolean, 
        default=True, 
        nullable=False, 
        comment="是否启用通知"
    )
    email_notification = Column(
        Boolean, 
        default=True, 
        nullable=False, 
        comment="是否启用邮件通知"
    )
    push_notification = Column(
        Boolean, 
        default=True, 
        nullable=False, 
        comment="是否启用推送通知"
    )

    # 关联到用户表
    user = relationship("User", backref="preferences", uselist=False)


class UserDefaultRole(BaseModel):
    """用户默认角色设置表，存储用户首次登录时的默认角色"""
    __tablename__ = "user_default_roles"
    __table_args__ = {"comment": "用户默认角色设置表，存储用户首次登录的默认角色"}

    id = Column(
        String(36), 
        primary_key=True, 
        default=generate_uuid, 
        comment="记录ID"
    )
    user_id = Column(
        String(36), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False,
        unique=True,
        comment="用户ID"
    )
    default_role = Column(
        String(50), 
        nullable=False, 
        comment="默认角色名称"
    )

    # 关联到用户表
    user = relationship("User", backref="default_role_setting", uselist=False)


class LoginHistory(BaseModel):
    """登录历史表，记录用户登录信息"""
    __tablename__ = "login_history"
    __table_args__ = {"comment": "登录历史表，记录用户登录信息"}

    id = Column(
        String(36), 
        primary_key=True, 
        default=generate_uuid, 
        comment="登录记录ID"
    )
    user_id = Column(
        String(36), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, 
        comment="用户ID"
    )
    ip_address = Column(
        String(45), 
        nullable=True, 
        comment="登录IP地址"
    )
    user_agent = Column(
        Text, 
        nullable=True, 
        comment="用户代理信息"
    )
    login_time = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False, 
        comment="登录时间"
    )
    login_role = Column(
        String(50), 
        nullable=True, 
        comment="登录时使用的角色"
    )
    location = Column(
        String(100), 
        nullable=True, 
        comment="登录地点"
    )

    # 关联到用户表
    user = relationship("User", backref="login_histories") 