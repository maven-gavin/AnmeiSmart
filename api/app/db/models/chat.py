from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.models.base_model import BaseModel
from app.db.uuid_utils import conversation_id, message_id, profile_id


class Conversation(BaseModel):
    """聊天会话数据库模型"""
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=conversation_id)
    title = Column(String, nullable=False)
    customer_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    assigned_consultant_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)

    # 关联关系
    customer = relationship("User", backref="conversations", foreign_keys=[customer_id])
    assigned_consultant = relationship("User", foreign_keys=[assigned_consultant_id])
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(BaseModel):
    """聊天消息数据库模型"""
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=message_id)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    type = Column(Enum("text", "image", "voice", "file", "system", name="message_type"), default="text")
    sender_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    sender_type = Column(Enum("customer", "consultant", "doctor", "ai", "system", name="sender_type"), nullable=False)
    is_read = Column(Boolean, default=False)
    is_important = Column(Boolean, default=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # 关联关系
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])


class CustomerProfile(BaseModel):
    """客户档案数据库模型，扩展用户信息"""
    __tablename__ = "customer_profiles"

    id = Column(String(36), primary_key=True, default=profile_id)
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    medical_history = Column(Text, nullable=True)
    allergies = Column(Text, nullable=True)  # 存储为JSON字符串
    preferences = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)  # 存储为JSON字符串

    # 关联关系
    user = relationship("User", backref="profile", uselist=False) 