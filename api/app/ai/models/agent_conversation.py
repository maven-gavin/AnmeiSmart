from sqlalchemy import Column, String, Text, Integer, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship

from app.common.models.base_model import BaseModel
from app.common.deps.uuid_utils import generate_agent_conversation_id


class AgentConversation(BaseModel):
    """Agent 会话表（本地持久化，替代 Dify conversations）。"""

    __tablename__ = "agent_conversations"
    __table_args__ = (
        Index("idx_agent_conv_config_user", "agent_config_id", "user_id"),
        Index("idx_agent_conv_updated", "updated_at"),
        {"comment": "Agent 会话表"},
    )

    id = Column(String(36), primary_key=True, default=generate_agent_conversation_id, comment="会话ID")
    agent_config_id = Column(String(36), ForeignKey("agent_configs.id", ondelete="CASCADE"), nullable=False, comment="Agent配置ID")
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    title = Column(String(255), nullable=False, default="新对话", comment="会话标题")

    messages = relationship("AgentMessage", back_populates="conversation", cascade="all, delete-orphan")
