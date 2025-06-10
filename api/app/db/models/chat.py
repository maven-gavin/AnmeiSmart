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
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.timestamp")
    upload_sessions = relationship("UploadSession", back_populates="conversation", cascade="all, delete-orphan")


class Message(BaseModel):
    """聊天消息数据库模型，存储会话中的消息内容
    
    支持统一消息模型的四种类型：
    - text: 纯文本消息
    - media: 媒体文件消息（图片、语音、视频、文档等）
    - system: 系统事件消息（如用户加入、接管状态等）
    - structured: 结构化卡片消息（预约确认、服务推荐等）
    """
    __tablename__ = "messages"
    __table_args__ = {"comment": "聊天消息表，存储会话中的消息内容"}

    id = Column(String(36), primary_key=True, default=message_id, comment="消息ID")
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True, comment="会话ID")
    
    # 结构化的消息内容，支持不同类型的内容结构
    content = Column(JSON, nullable=False, comment="结构化的消息内容 (JSON格式)")
    
    # 四种统一消息类型
    type = Column(Enum("text", "media", "system", "structured", name="message_type"), nullable=False, index=True, comment="消息主类型")
    
    sender_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True, comment="发送者用户ID")
    sender_type = Column(Enum("customer", "consultant", "doctor", "ai", "system", name="sender_type"), nullable=False, comment="发送者在发送消息时的角色")
    
    # 状态字段
    is_read = Column(Boolean, default=False, comment="是否已读")
    is_important = Column(Boolean, default=False, comment="是否重要")
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), comment="消息时间戳")

    # 高级功能字段
    reply_to_message_id = Column(String(36), ForeignKey("messages.id"), nullable=True, comment="回复的消息ID")
    reactions = Column(JSON, nullable=True, comment="消息回应，格式: {'👍': ['user_id1', 'user_id2'], '❤️': ['user_id3']}")
    extra_metadata = Column(JSON, nullable=True, comment="附加元数据，如: {'upload_method': 'file_picker', 'client_info': {...}}")

    # 关联关系
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
    reply_to_message = relationship("Message", remote_side=[id], backref="replies") 