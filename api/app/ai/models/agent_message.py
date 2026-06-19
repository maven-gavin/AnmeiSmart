from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship

from app.common.models.base_model import BaseModel
from app.common.deps.uuid_utils import generate_agent_message_id, generate_uuid


class AgentMessage(BaseModel):
    """Agent 消息表。"""

    __tablename__ = "agent_messages"
    __table_args__ = (
        Index("idx_agent_msg_conversation", "conversation_id", "created_at"),
        {"comment": "Agent 消息表"},
    )

    id = Column(String(36), primary_key=True, default=generate_agent_message_id, comment="消息ID")
    conversation_id = Column(String(36), ForeignKey("agent_conversations.id", ondelete="CASCADE"), nullable=False, comment="会话ID")
    role = Column(String(20), nullable=False, comment="角色: user | assistant")
    content = Column(Text, nullable=False, default="", comment="消息内容")
    is_error = Column(Boolean, default=False, nullable=False, comment="是否错误消息")
    extra_metadata = Column("metadata", JSON, nullable=True, comment="扩展元数据(thoughts/files/task_id)")

    conversation = relationship("AgentConversation", back_populates="messages")


class AgentMessageFeedback(BaseModel):
    """Agent 消息反馈。"""

    __tablename__ = "agent_message_feedbacks"
    __table_args__ = (
        Index("idx_agent_feedback_message_user", "message_id", "user_id", unique=True),
        {"comment": "Agent 消息反馈表"},
    )

    id = Column(String(36), primary_key=True, default=generate_uuid, comment="反馈ID")
    message_id = Column(String(36), ForeignKey("agent_messages.id", ondelete="CASCADE"), nullable=False, comment="消息ID")
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    rating = Column(String(20), nullable=False, comment="like | dislike")
