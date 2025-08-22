from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Enum, JSON, Integer, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.models.base_model import BaseModel
from app.db.uuid_utils import conversation_id, message_id


class Conversation(BaseModel):
    """会话聚合根 - 存储会话信息和权限控制"""
    __tablename__ = "conversations"
    __table_args__ = (
        Index('idx_conversation_owner', 'owner_id'),
        Index('idx_conversation_type', 'type'),
        Index('idx_conversation_status', 'is_active'),
        Index('idx_conversation_consultation', 'is_consultation_session'),
        Index('idx_conversation_pinned', 'is_pinned', 'pinned_at'),
        Index('idx_conversation_first_participant', 'first_participant_id'),
        {"comment": "会话表，存储用户会话信息"}
    )

    id = Column(String(36), primary_key=True, default=conversation_id, comment="会话ID")
    title = Column(String, nullable=False, comment="会话标题")
    
    # 会话类型
    type = Column(String(50), nullable=False, default="single", comment="会话类型：单聊、群聊")
    
    # 会话所有者（拥有该会话的所有权限）
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False, comment="会话所有者用户ID")
    
    # 新增：咨询类会话标识
    is_consultation_session = Column(Boolean, default=False, comment="是否为咨询类会话")
    
    # 新增：置顶功能
    is_pinned = Column(Boolean, default=False, comment="是否置顶")
    pinned_at = Column(DateTime(timezone=True), nullable=True, comment="置顶时间")
    
    # 新增：第一个参与者ID（优化好友单聊查询）
    first_participant_id = Column(String(36), ForeignKey("users.id"), nullable=True, comment="第一个参与者用户ID")
    
    # 会话状态
    is_active = Column(Boolean, default=True, comment="会话是否激活")
    is_archived = Column(Boolean, default=False, comment="是否已归档")
    
    # 统计信息
    message_count = Column(Integer, default=0, comment="消息总数")
    unread_count = Column(Integer, default=0, comment="未读消息数")
    last_message_at = Column(DateTime(timezone=True), nullable=True, comment="最后消息时间")
    
    # 关联关系
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_conversations")
    first_participant = relationship("User", foreign_keys=[first_participant_id])
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    participants = relationship("ConversationParticipant", back_populates="conversation", cascade="all, delete-orphan")


class Message(BaseModel):
    """消息实体 - 存储会话中的消息内容"""
    __tablename__ = "messages"
    __table_args__ = (
        Index('idx_message_conversation', 'conversation_id'),
        Index('idx_message_sender', 'sender_id'),
        Index('idx_message_sender_dh', 'sender_digital_human_id'),
        Index('idx_message_timestamp', 'timestamp'),
        {"comment": "消息表，存储会话中的消息内容"}
    )

    id = Column(String(36), primary_key=True, default=message_id, comment="消息ID")
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), 
                            nullable=False, comment="会话ID")
    
    # 消息内容
    content = Column(JSON, nullable=False, comment="结构化的消息内容 (JSON格式)")
    type = Column(Enum("text", "media", "system", "structured", name="message_type"), 
                  nullable=False, comment="消息主类型")
    
    # 发送者信息（支持数字人发送）
    sender_id = Column(String(36), ForeignKey("users.id"), nullable=True, comment="发送者用户ID")
    sender_digital_human_id = Column(String(36), ForeignKey("digital_humans.id"), nullable=True, 
                                    comment="发送者数字人ID")
    sender_type = Column(Enum("customer", "consultant", "doctor", "system", "digital_human", name="sender_type"), 
                         nullable=False, comment="发送者类型")
    
    # 消息状态
    is_read = Column(Boolean, default=False, comment="是否已读")
    is_important = Column(Boolean, default=False, comment="是否重要")
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), comment="消息时间戳")
    
    # 半接管状态下的确认机制
    requires_confirmation = Column(Boolean, default=False, comment="是否需要确认（半接管模式）")
    is_confirmed = Column(Boolean, default=True, comment="是否已确认")
    confirmed_by = Column(String(36), ForeignKey("users.id"), nullable=True, comment="确认人ID")
    confirmed_at = Column(DateTime(timezone=True), nullable=True, comment="确认时间")
    
    # 高级功能
    reply_to_message_id = Column(String(36), ForeignKey("messages.id"), nullable=True, comment="回复的消息ID")
    reactions = Column(JSON, nullable=True, comment="消息回应")
    extra_metadata = Column(JSON, nullable=True, comment="附加元数据")

    # 关联关系
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
    sender_digital_human = relationship("DigitalHuman", foreign_keys=[sender_digital_human_id])
    confirmed_by_user = relationship("User", foreign_keys=[confirmed_by])
    reply_to_message = relationship("Message", remote_side=[id], backref="replies")
    attachments = relationship("MessageAttachment", back_populates="message", cascade="all, delete-orphan")


class ConversationParticipant(BaseModel):
    """会话参与者实体 - 管理会话参与者和接管状态"""
    __tablename__ = "conversation_participants"
    __table_args__ = (
        Index('idx_conversation_participant_conv', 'conversation_id'),
        Index('idx_conversation_participant_user', 'user_id'),
        Index('idx_conversation_participant_dh', 'digital_human_id'),
        {"comment": "会话参与者表，支持用户和数字人参与"}
    )

    id = Column(String(36), primary_key=True, default=message_id, comment="参与者ID")
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False, comment="会话ID")
    
    # 参与者信息（用户或数字人）
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, comment="用户ID")
    digital_human_id = Column(String(36), ForeignKey("digital_humans.id"), nullable=True, comment="数字人ID")
    
    # 参与者角色
    role = Column(Enum("owner", "admin", "member", "guest", name="participant_role"), 
                  default="member", comment="参与者角色")
    
    # 接管状态（核心业务逻辑）
    takeover_status = Column(Enum("full_takeover", "semi_takeover", "no_takeover", name="takeover_status"), 
                            default="no_takeover", comment="接管状态：全接管、半接管、不接管")
    
    # 参与状态
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), comment="加入时间")
    left_at = Column(DateTime(timezone=True), nullable=True, comment="离开时间")
    is_active = Column(Boolean, default=True, comment="是否活跃")
    
    # 个人设置
    is_muted = Column(Boolean, default=False, comment="个人免打扰")
    last_read_at = Column(DateTime(timezone=True), nullable=True, comment="最后阅读时间")
    
    # 关联关系
    conversation = relationship("Conversation", back_populates="participants")
    user = relationship("User")
    digital_human = relationship("DigitalHuman")
    
    def __repr__(self):
        participant = self.user_id or self.digital_human_id
        return f"<ConversationParticipant(conv_id={self.conversation_id}, participant={participant})>" 