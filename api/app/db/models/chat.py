import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Conversation(Base):
    """聊天会话数据库模型"""
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=lambda: f"conv_{uuid.uuid4().hex}")
    title = Column(String, nullable=False)
    customer_id = Column(String, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关联关系
    customer = relationship("User", backref="conversations", foreign_keys=[customer_id])
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """聊天消息数据库模型"""
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: f"msg_{uuid.uuid4().hex}")
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    type = Column(Enum("text", "image", "voice", "file", "system", name="message_type"), default="text")
    sender_id = Column(String, ForeignKey("users.id"), nullable=False)
    sender_type = Column(Enum("customer", "consultant", "doctor", "ai", "system", name="sender_type"), nullable=False)
    is_read = Column(Boolean, default=False)
    is_important = Column(Boolean, default=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # 关联关系
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])


class CustomerProfile(Base):
    """客户档案数据库模型，扩展用户信息"""
    __tablename__ = "customer_profiles"

    id = Column(String, primary_key=True, default=lambda: f"prof_{uuid.uuid4().hex}")
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    medical_history = Column(Text, nullable=True)
    allergies = Column(Text, nullable=True)  # 存储为JSON字符串
    preferences = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)  # 存储为JSON字符串
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关联关系
    user = relationship("User", backref="profile", uselist=False) 