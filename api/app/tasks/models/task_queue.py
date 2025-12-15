from sqlalchemy import Column, String, Text, Boolean, Enum, JSON, Index

from app.common.models.base_model import BaseModel


class TaskQueue(BaseModel):
    """任务队列（M0占位）- 用于场景化自动分配的配置载体"""

    __tablename__ = "task_queues"
    __table_args__ = (
        Index("idx_task_queue_scene_key", "scene_key"),
        Index("idx_task_queue_is_active", "is_active"),
        {"comment": "任务队列表（M0占位），用于后续按场景/轮值进行自动分配"},
    )

    name = Column(String(200), nullable=False, comment="队列名称（唯一标识建议）")
    scene_key = Column(String(100), nullable=False, comment="场景Key，如 sales_delivery")
    description = Column(Text, nullable=True, comment="队列描述")

    rotation_strategy = Column(
        Enum("fixed", "round_robin", name="task_queue_rotation_strategy"),
        nullable=False,
        default="fixed",
        comment="分配策略：fixed固定负责人，round_robin轮值",
    )
    config = Column(JSON, nullable=True, comment="队列配置（轮值成员/规则等，JSON）")

    is_active = Column(Boolean, nullable=False, default=True, comment="是否启用")


