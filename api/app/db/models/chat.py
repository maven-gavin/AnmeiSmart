from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.models.base_model import BaseModel
from app.db.uuid_utils import conversation_id, message_id


class Conversation(BaseModel):
    """聊天会话数据库模型，存储用户与顾问的会话信息"""
    __tablename__ = "conversations"
    __table_args__ = {"comment": "聊天会话表，存储用户与顾问的会话信息"}

    id = Column(String(36), primary_key=True, default=conversation_id, comment="会话ID")
    title = Column(String, nullable=False, comment="会话标题")
    customer_id = Column(String(36), ForeignKey("users.id"), nullable=False, comment="顾客用户ID")
    assigned_consultant_id = Column(String(36), ForeignKey("users.id"), nullable=True, comment="分配的顾问用户ID")
    is_active = Column(Boolean, default=True, comment="会话是否激活")
    consultation_type = Column(String, nullable=True, comment="咨询类型")
    summary = Column(Text, nullable=True, comment="会话总结")
    is_ai_controlled = Column(Boolean, default=True, comment="当前会话是否由AI控制（True=AI，False=顾问接管）")

    # 关联关系
    customer = relationship("User", backref="conversations", foreign_keys=[customer_id])
    assigned_consultant = relationship("User", foreign_keys=[assigned_consultant_id])
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(BaseModel):
    """聊天消息数据库模型，存储会话中的消息内容"""
    __tablename__ = "messages"
    __table_args__ = {"comment": "聊天消息表，存储会话中的消息内容"}

    id = Column(String(36), primary_key=True, default=message_id, comment="消息ID")
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, comment="会话ID")
    content = Column(Text, nullable=False, comment="消息内容")
    type = Column(Enum("text", "image", "voice", "file", "system", name="message_type"), default="text", comment="消息类型")
    sender_id = Column(String(36), ForeignKey("users.id"), nullable=False, comment="发送者用户ID")
    sender_type = Column(Enum("customer", "consultant", "doctor", "ai", "system", name="sender_type"), nullable=False, comment="发送者类型")
    is_read = Column(Boolean, default=False, comment="是否已读")
    is_important = Column(Boolean, default=False, comment="是否重要")
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), comment="消息时间戳")

    # 关联关系
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id]) 