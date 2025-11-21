from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Enum, JSON, Integer, Index
from sqlalchemy.orm import relationship

from app.common.infrastructure.db.base_model import BaseModel
from app.common.infrastructure.db.uuid_utils import digital_human_id, task_id


class DigitalHuman(BaseModel):
    """数字人聚合根 - 存储数字人基础信息和配置"""
    __tablename__ = "digital_humans"
    __table_args__ = (
        Index('idx_digital_human_user', 'user_id'),
        Index('idx_digital_human_status', 'status'),
        Index('idx_digital_human_type', 'type'),
        {"comment": "数字人表，存储数字人基础信息和配置"}
    )

    id = Column(String(36), primary_key=True, default=digital_human_id, comment="数字人ID")
    name = Column(String(255), nullable=False, comment="数字人名称")
    avatar = Column(String(1024), nullable=True, comment="数字人头像URL")
    description = Column(Text, nullable=True, comment="数字人描述")
    
    # 数字人类型和状态
    type = Column(Enum("personal", "business", "specialized", "system", name="digital_human_type"), 
                  default="personal", comment="数字人类型：个人、商务、专业、系统")
    status = Column(Enum("active", "inactive", "maintenance", name="digital_human_status"), 
                    default="active", comment="数字人状态")
    is_system_created = Column(Boolean, default=False, comment="是否系统创建（系统创建的不可删除）")
    
    # 个性化配置
    personality = Column(JSON, nullable=True, comment="性格特征配置")
    greeting_message = Column(Text, nullable=True, comment="默认打招呼消息")
    welcome_message = Column(Text, nullable=True, comment="欢迎消息模板")
    
    # 关联用户（数字人属于哪个用户）
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, comment="所属用户ID")
    
    # 统计信息
    conversation_count = Column(Integer, default=0, comment="会话总数")
    message_count = Column(Integer, default=0, comment="消息总数")
    last_active_at = Column(DateTime(timezone=True), nullable=True, comment="最后活跃时间")
    
    # 关联关系
    user = relationship("app.identity_access.models.user.User", back_populates="digital_humans")
    agent_configs = relationship("app.digital_humans.infrastructure.db.digital_human.DigitalHumanAgentConfig", back_populates="digital_human", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<DigitalHuman(id={self.id}, name={self.name}, user_id={self.user_id})>"


class DigitalHumanAgentConfig(BaseModel):
    """数字人与智能体配置的多对多关联表"""
    __tablename__ = "digital_human_agent_configs"
    __table_args__ = (
        Index('idx_dh_agent_digital_human', 'digital_human_id'),
        Index('idx_dh_agent_config', 'agent_config_id'),
        Index('idx_dh_agent_priority', 'priority'),
        {"comment": "数字人与智能体配置关联表，支持多对多关系"}
    )

    id = Column(String(36), primary_key=True, default=digital_human_id, comment="关联ID")
    digital_human_id = Column(String(36), ForeignKey("digital_humans.id", ondelete="CASCADE"), 
                             nullable=False, comment="数字人ID")
    agent_config_id = Column(String(36), ForeignKey("agent_configs.id", ondelete="CASCADE"), 
                           nullable=False, comment="智能体配置ID")
    
    # 配置参数
    priority = Column(Integer, default=1, comment="优先级（数字越小优先级越高）")
    is_active = Column(Boolean, default=True, comment="是否启用此配置")
    
    # 使用场景配置
    scenarios = Column(JSON, nullable=True, comment="适用场景配置")
    context_prompt = Column(Text, nullable=True, comment="上下文提示词")
    
    # 关联关系
    digital_human = relationship("app.digital_humans.infrastructure.db.digital_human.DigitalHuman", back_populates="agent_configs")
    agent_config = relationship("app.ai.infrastructure.db.agent_config.AgentConfig")
    
    def __repr__(self):
        return f"<DigitalHumanAgentConfig(dh_id={self.digital_human_id}, agent_id={self.agent_config_id})>"
