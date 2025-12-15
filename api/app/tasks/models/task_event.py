from sqlalchemy import Column, String, JSON, Index

from app.common.models.base_model import BaseModel


class TaskEvent(BaseModel):
    """任务事件流水（M0占位）- 记录“谁在何时做了什么”"""

    __tablename__ = "task_events"
    __table_args__ = (
        Index("idx_task_event_task_id", "task_id"),
        Index("idx_task_event_event_type", "event_type"),
        {"comment": "任务事件表（M0占位），用于审计与回放"},
    )

    task_id = Column(String(36), nullable=False, comment="任务ID")
    event_type = Column(String(100), nullable=False, comment="事件类型，如 status_changed/claimed/assigned/commented")
    payload = Column(JSON, nullable=True, comment="事件载荷（JSON）")


