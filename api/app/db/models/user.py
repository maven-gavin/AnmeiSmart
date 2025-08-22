from sqlalchemy import Boolean, Column, String, DateTime, ForeignKey, Table, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.models.base_model import BaseModel, TimestampMixin
from app.db.base import Base
from app.db.uuid_utils import user_id, role_id


class AdminLevel(str, enum.Enum):
    """管理员级别枚举"""
    BASIC = "basic"           # 基础管理员
    ADVANCED = "advanced"     # 高级管理员
    SUPER = "super"           # 超级管理员

# 用户-角色关联表 (使用String类型的外键)
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, comment="用户ID"),
    Column("role_id", String(36), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True, comment="角色ID"),
    Column("assigned_at", DateTime(timezone=True), server_default=func.now(), comment="分配时间")
)

class Role(BaseModel):
    """角色数据库模型，存储系统中所有角色信息"""
    __tablename__ = "roles"
    __table_args__ = {"comment": "角色表，存储系统所有角色信息"}

    id = Column(String(36), primary_key=True, default=role_id, comment="角色ID")
    name = Column(String, unique=True, index=True, nullable=False, comment="角色名称")
    description = Column(String, nullable=True, comment="角色描述")

    # 角色关联的用户
    users = relationship("User", secondary="user_roles", back_populates="roles")

class User(BaseModel):
    """用户基础数据库模型，存储所有类型用户共有的信息"""
    __tablename__ = "users"
    __table_args__ = {"comment": "用户表，存储所有用户基础信息"}

    id = Column(String(36), primary_key=True, default=user_id, comment="用户ID")
    email = Column(String, unique=True, index=True, nullable=False, comment="邮箱")
    username = Column(String, unique=True, index=True, nullable=False, comment="用户名")
    hashed_password = Column(String, nullable=False, comment="加密密码")
    phone = Column(String, unique=True, index=True, nullable=True, comment="手机号")
    avatar = Column(String, nullable=True, comment="头像URL")
    is_active = Column(Boolean, default=True, comment="是否激活")
    
    # 用户角色关联
    roles = relationship("Role", secondary="user_roles", back_populates="users")
    
    # 扩展表关联
    customer = relationship("Customer", back_populates="user", uselist=False, cascade="all, delete-orphan")
    doctor = relationship("Doctor", back_populates="user", uselist=False, cascade="all, delete-orphan")
    consultant = relationship("Consultant", back_populates="user", uselist=False, cascade="all, delete-orphan")
    operator = relationship("Operator", back_populates="user", uselist=False, cascade="all, delete-orphan")
    administrator = relationship("Administrator", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    # 上传会话关联
    upload_sessions = relationship("UploadSession", back_populates="user", cascade="all, delete-orphan")
    
    # 数字人关联（新增）
    digital_humans = relationship("DigitalHuman", back_populates="user", cascade="all, delete-orphan")
    owned_conversations = relationship("Conversation", foreign_keys="Conversation.owner_id", back_populates="owner")
    created_tasks = relationship("PendingTask", foreign_keys="PendingTask.created_by")
    assigned_tasks = relationship("PendingTask", foreign_keys="PendingTask.assigned_to")
    
    # 通讯录关联（新增）
    friendships = relationship("Friendship", foreign_keys="Friendship.user_id", 
                              back_populates="user", cascade="all, delete-orphan")
    contact_tags = relationship("ContactTag", back_populates="user", cascade="all, delete-orphan")
    contact_groups = relationship("ContactGroup", back_populates="user", cascade="all, delete-orphan")
    contact_privacy_setting = relationship("ContactPrivacySetting", back_populates="user", 
                                          uselist=False, cascade="all, delete-orphan")

class Doctor(BaseModel):
    """医生特有信息表，存储医生扩展信息"""
    __tablename__ = "doctors"
    __table_args__ = {"comment": "医生表，存储医生扩展信息"}
    
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False, comment="用户ID")
    specialization = Column(String, nullable=True, comment="专科方向")
    certification = Column(String, nullable=True, comment="资格证书")
    license_number = Column(String, nullable=True, comment="执业证号")
    
    # 关联到基础用户表
    user = relationship("User", back_populates="doctor")

class Consultant(BaseModel):
    """医美顾问特有信息表，存储顾问扩展信息"""
    __tablename__ = "consultants"
    __table_args__ = {"comment": "医美顾问表，存储顾问扩展信息"}
    
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False, comment="用户ID")
    expertise = Column(String, nullable=True, comment="专长领域")
    performance_metrics = Column(Text, nullable=True, comment="业绩指标")
    
    # 关联到基础用户表
    user = relationship("User", back_populates="consultant")

class Operator(BaseModel):
    """机构运营人员特有信息表，存储运营人员扩展信息"""
    __tablename__ = "operators"
    __table_args__ = {"comment": "运营人员表，存储机构运营人员扩展信息"}
    
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False, comment="用户ID")
    department = Column(String, nullable=True, comment="所属部门")
    responsibilities = Column(Text, nullable=True, comment="职责描述")
    
    # 关联到基础用户表
    user = relationship("User", back_populates="operator")

class Administrator(BaseModel):
    """系统管理员特有信息表，存储管理员扩展信息"""
    __tablename__ = "administrators"
    __table_args__ = {"comment": "系统管理员表，存储管理员扩展信息"}
    
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False, comment="用户ID")
    admin_level = Column(String, default=AdminLevel.BASIC, comment="管理员级别")
    access_permissions = Column(Text, nullable=True, comment="权限描述")
    
    # 关联到基础用户表
    user = relationship("User", back_populates="administrator") 