from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Table, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

# 用户-角色关联表 (简化版本，移除额外外键)
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("assigned_at", DateTime(timezone=True), server_default=func.now())
)

class Role(Base):
    """角色数据库模型"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 角色关联的用户
    users = relationship("User", secondary="user_roles", back_populates="roles")

class User(Base):
    """用户基础数据库模型，存储所有类型用户共有的信息"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    phone = Column(String, unique=True, index=True, nullable=True)
    avatar = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 用户角色关联
    roles = relationship("Role", secondary="user_roles", back_populates="users")
    
    # 扩展表关联
    customer = relationship("Customer", back_populates="user", uselist=False, cascade="all, delete-orphan")
    doctor = relationship("Doctor", back_populates="user", uselist=False, cascade="all, delete-orphan")
    consultant = relationship("Consultant", back_populates="user", uselist=False, cascade="all, delete-orphan")
    operator = relationship("Operator", back_populates="user", uselist=False, cascade="all, delete-orphan")
    administrator = relationship("Administrator", back_populates="user", uselist=False, cascade="all, delete-orphan")

class Customer(Base):
    """顾客特有信息表"""
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    medical_history = Column(Text, nullable=True)
    allergies = Column(Text, nullable=True)
    preferences = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关联到基础用户表
    user = relationship("User", back_populates="customer")

class Doctor(Base):
    """医生特有信息表"""
    __tablename__ = "doctors"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    specialization = Column(String, nullable=True)
    certification = Column(String, nullable=True)
    license_number = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关联到基础用户表
    user = relationship("User", back_populates="doctor")

class Consultant(Base):
    """医美顾问特有信息表"""
    __tablename__ = "consultants"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    expertise = Column(String, nullable=True)
    performance_metrics = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关联到基础用户表
    user = relationship("User", back_populates="consultant")

class Operator(Base):
    """机构运营人员特有信息表"""
    __tablename__ = "operators"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    department = Column(String, nullable=True)
    responsibilities = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关联到基础用户表
    user = relationship("User", back_populates="operator")

class Administrator(Base):
    """系统管理员特有信息表"""
    __tablename__ = "administrators"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    admin_level = Column(Integer, default=1)
    access_permissions = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关联到基础用户表
    user = relationship("User", back_populates="administrator") 