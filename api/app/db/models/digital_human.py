from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Enum, JSON, Integer, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import Optional

from app.db.models.base_model import BaseModel
from app.db.uuid_utils import digital_human_id, consultation_id, task_id


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
    user = relationship("User", back_populates="digital_humans")
    agent_configs = relationship("DigitalHumanAgentConfig", back_populates="digital_human", cascade="all, delete-orphan")
    
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
    digital_human = relationship("DigitalHuman", back_populates="agent_configs")
    agent_config = relationship("AgentConfig")
    
    def __repr__(self):
        return f"<DigitalHumanAgentConfig(dh_id={self.digital_human_id}, agent_id={self.agent_config_id})>"


class ConsultationRecord(BaseModel):
    """咨询记录聚合根 - 独立管理咨询业务"""
    __tablename__ = "consultation_records"
    __table_args__ = (
        Index('idx_consultation_conversation', 'conversation_id'),
        Index('idx_consultation_customer', 'customer_id'),
        Index('idx_consultation_consultant', 'consultant_id'),
        Index('idx_consultation_type', 'consultation_type'),
        {"comment": "咨询记录表，记录每次咨询的详细信息"}
    )

    id = Column(String(36), primary_key=True, default=consultation_id, comment="咨询记录ID")
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False, comment="关联会话ID")
    
    # 参与人员
    customer_id = Column(String(36), ForeignKey("users.id"), nullable=False, comment="客户ID")
    consultant_id = Column(String(36), ForeignKey("users.id"), nullable=True, comment="顾问ID")
    digital_human_id = Column(String(36), ForeignKey("digital_humans.id"), nullable=True, comment="数字人ID")
    
    # 咨询信息
    consultation_type = Column(Enum("initial", "follow_up", "emergency", "specialized", "other", name="consultation_type"), 
                              nullable=False, comment="咨询类型")
    title = Column(String(500), nullable=False, comment="咨询标题")
    description = Column(Text, nullable=True, comment="咨询描述")
    
    # 咨询状态
    status = Column(Enum("pending", "in_progress", "completed", "cancelled", name="consultation_status"), 
                    default="pending", comment="咨询状态")
    
    # 时间信息
    started_at = Column(DateTime(timezone=True), nullable=True, comment="开始时间")
    ended_at = Column(DateTime(timezone=True), nullable=True, comment="结束时间")
    duration_minutes = Column(Integer, nullable=True, comment="持续时间（分钟）")
    
    # 咨询结果
    consultation_summary = Column(JSON, nullable=True, comment="结构化咨询总结")
    satisfaction_rating = Column(Integer, nullable=True, comment="满意度评分（1-5）")
    follow_up_required = Column(Boolean, default=False, comment="是否需要跟进")
    
    # 关联关系
    conversation = relationship("Conversation")
    customer = relationship("User", foreign_keys=[customer_id])
    consultant = relationship("User", foreign_keys=[consultant_id])
    digital_human = relationship("DigitalHuman", foreign_keys=[digital_human_id])
    
    def __repr__(self):
        return f"<ConsultationRecord(id={self.id}, type={self.consultation_type}, customer_id={self.customer_id})>"


class PendingTask(BaseModel):
    """待办任务聚合根 - 管理系统任务和工作流"""
    __tablename__ = "pending_tasks"
    __table_args__ = (
        Index('idx_pending_task_type', 'task_type'),
        Index('idx_pending_task_status', 'status'),
        Index('idx_pending_task_assignee', 'assigned_to'),
        Index('idx_pending_task_priority', 'priority'),
        {"comment": "待办任务表，记录系统发出的待处理任务"}
    )

    id = Column(String(36), primary_key=True, default=task_id, comment="任务ID")
    
    # 任务基础信息
    title = Column(String(500), nullable=False, comment="任务标题")
    description = Column(Text, nullable=True, comment="任务描述")
    task_type = Column(String(100), nullable=False, comment="任务类型")
    
    # 任务状态和优先级
    status = Column(Enum("pending", "assigned", "in_progress", "completed", "cancelled", name="task_status"), 
                    default="pending", comment="任务状态")
    priority = Column(Enum("low", "medium", "high", "urgent", name="task_priority"), 
                     default="medium", comment="任务优先级")
    
    # 任务分配
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True, comment="创建人ID")
    assigned_to = Column(String(36), ForeignKey("users.id"), nullable=True, comment="分配给用户ID")
    assigned_at = Column(DateTime(timezone=True), nullable=True, comment="分配时间")
    
    # 关联业务对象
    related_object_type = Column(String(100), nullable=True, comment="关联对象类型")
    related_object_id = Column(String(36), nullable=True, comment="关联对象ID")
    
    # 任务数据
    task_data = Column(JSON, nullable=True, comment="任务相关数据")
    
    # 时间信息
    due_date = Column(DateTime(timezone=True), nullable=True, comment="截止时间")
    completed_at = Column(DateTime(timezone=True), nullable=True, comment="完成时间")
    
    # 处理结果
    result = Column(JSON, nullable=True, comment="处理结果")
    notes = Column(Text, nullable=True, comment="处理备注")
    
    # 关联关系
    created_by_user = relationship("User", foreign_keys=[created_by], overlaps="created_tasks")
    assigned_to_user = relationship("User", foreign_keys=[assigned_to], overlaps="assigned_tasks")
    
    def __repr__(self):
        return f"<PendingTask(id={self.id}, type={self.task_type}, status={self.status})>"
