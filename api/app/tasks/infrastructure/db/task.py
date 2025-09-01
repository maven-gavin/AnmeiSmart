from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Enum, JSON, Index
from sqlalchemy.orm import relationship

from app.common.infrastructure.db.base_model import BaseModel
from app.common.infrastructure.db.uuid_utils import task_id

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
