from sqlalchemy import Column, DateTime, Index, Integer, String, Text, UniqueConstraint

from app.common.models.base_model import BaseModel


class DatahubWorkerHeartbeat(BaseModel):
    __tablename__ = "datahub_worker_heartbeat"
    __table_args__ = (
        UniqueConstraint("worker_name", name="uq_datahub_worker_heartbeat_worker_name"),
        Index("idx_datahub_worker_heartbeat_last_heartbeat_at", "last_heartbeat_at"),
        {"comment": "DataHub Worker 心跳状态"},
    )

    worker_name = Column(String(100), nullable=False, comment="Worker 名称")
    status = Column(String(20), nullable=False, default="idle", comment="状态：idle/running/error")
    last_heartbeat_at = Column(DateTime(timezone=True), nullable=False, comment="最近心跳时间")
    last_run_id = Column(String(36), nullable=True, comment="最近处理的作业ID")
    processed_count = Column(Integer, nullable=False, default=0, comment="累计处理作业数")
    last_error = Column(Text, nullable=True, comment="最近错误")
