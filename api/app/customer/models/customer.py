from sqlalchemy import Column, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.common.models.base_model import BaseModel
from app.common.deps.uuid_utils import profile_id

class Customer(BaseModel):
    """客户特有信息表，存储客户扩展信息"""
    __tablename__ = "customers"
    __table_args__ = {"comment": "客户表，存储客户扩展信息"}
    
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False, comment="用户ID")
    medical_history = Column(Text, nullable=True, comment="病史")
    allergies = Column(Text, nullable=True, comment="过敏史")
    preferences = Column(Text, nullable=True, comment="偏好")
    
    # 关联到基础用户表
    user = relationship("app.identity_access.models.user.User", back_populates="customer")
    
    # 关联到客户档案
    profile = relationship("CustomerProfile", back_populates="customer", uselist=False, cascade="all, delete-orphan")

class CustomerProfile(BaseModel):
    """客户档案数据库模型，扩展客户信息"""
    __tablename__ = "customer_profiles"
    __table_args__ = {"comment": "客户档案表，扩展客户详细信息"}

    id = Column(String(36), primary_key=True, default=profile_id, comment="档案ID")
    customer_id = Column(String(36), ForeignKey("customers.user_id"), unique=True, nullable=False, comment="客户用户ID")
    medical_history = Column(Text, nullable=True, comment="病史")
    allergies = Column(Text, nullable=True, comment="过敏史（JSON字符串）")
    preferences = Column(Text, nullable=True, comment="偏好")
    tags = Column(Text, nullable=True, comment="标签（JSON字符串）")
    risk_notes = Column(JSON, nullable=True, comment="风险提示信息")

    # 关联关系
    customer = relationship("Customer", back_populates="profile")

