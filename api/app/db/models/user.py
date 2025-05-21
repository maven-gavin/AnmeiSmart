from sqlalchemy import Boolean, Column, String, DateTime, ForeignKey, Table, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.models.base_model import BaseModel, TimestampMixin
from app.db.base import Base
from app.db.uuid_utils import user_id, role_id

# 用户-角色关联表 (使用String类型的外键)
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", String(36), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("assigned_at", DateTime(timezone=True), server_default=func.now())
)

class Role(BaseModel):
    """角色数据库模型"""
    __tablename__ = "roles"

    id = Column(String(36), primary_key=True, default=role_id)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)

    # 角色关联的用户
    users = relationship("User", secondary="user_roles", back_populates="roles")

class User(BaseModel):
    """用户基础数据库模型，存储所有类型用户共有的信息"""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=user_id)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    phone = Column(String, unique=True, index=True, nullable=True)
    avatar = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # 用户角色关联
    roles = relationship("Role", secondary="user_roles", back_populates="users")
    
    # 扩展表关联
    customer = relationship("Customer", back_populates="user", uselist=False, cascade="all, delete-orphan")
    doctor = relationship("Doctor", back_populates="user", uselist=False, cascade="all, delete-orphan")
    consultant = relationship("Consultant", back_populates="user", uselist=False, cascade="all, delete-orphan")
    operator = relationship("Operator", back_populates="user", uselist=False, cascade="all, delete-orphan")
    administrator = relationship("Administrator", back_populates="user", uselist=False, cascade="all, delete-orphan")

class Customer(BaseModel):
    """顾客特有信息表"""
    __tablename__ = "customers"
    
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    medical_history = Column(Text, nullable=True)
    allergies = Column(Text, nullable=True)
    preferences = Column(Text, nullable=True)
    
    # 关联到基础用户表
    user = relationship("User", back_populates="customer")

class Doctor(BaseModel):
    """医生特有信息表"""
    __tablename__ = "doctors"
    
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    specialization = Column(String, nullable=True)
    certification = Column(String, nullable=True)
    license_number = Column(String, nullable=True)
    
    # 关联到基础用户表
    user = relationship("User", back_populates="doctor")

class Consultant(BaseModel):
    """医美顾问特有信息表"""
    __tablename__ = "consultants"
    
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    expertise = Column(String, nullable=True)
    performance_metrics = Column(Text, nullable=True)
    
    # 关联到基础用户表
    user = relationship("User", back_populates="consultant")

class Operator(BaseModel):
    """机构运营人员特有信息表"""
    __tablename__ = "operators"
    
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    department = Column(String, nullable=True)
    responsibilities = Column(Text, nullable=True)
    
    # 关联到基础用户表
    user = relationship("User", back_populates="operator")

class Administrator(BaseModel):
    """系统管理员特有信息表"""
    __tablename__ = "administrators"
    
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    admin_level = Column(String, default="1")
    access_permissions = Column(Text, nullable=True)
    
    # 关联到基础用户表
    user = relationship("User", back_populates="administrator") 