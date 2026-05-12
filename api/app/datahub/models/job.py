from sqlalchemy import JSON, Column, Date, DateTime, ForeignKey, Index, Integer, String, Text

from app.common.models.base_model import BaseModel


class DatahubJobRun(BaseModel):
    __tablename__ = "datahub_job_runs"
    __table_args__ = (
        Index("idx_datahub_job_runs_job_type", "job_type"),
        Index("idx_datahub_job_runs_status", "status"),
        Index("idx_datahub_job_runs_dataset", "dataset"),
        {"comment": "DataHub 作业运行记录"},
    )

    job_type = Column(String(50), nullable=False, comment="作业类型：backfill/daily_incremental")
    dataset = Column(String(100), nullable=True, comment="数据集")
    status = Column(String(20), nullable=False, default="pending", comment="状态")
    trigger_source = Column(String(50), nullable=True, comment="触发来源：api/cli/cron")
    job_params = Column(JSON, nullable=True, comment="作业参数快照")
    started_at = Column(DateTime(timezone=True), nullable=True, comment="开始时间")
    finished_at = Column(DateTime(timezone=True), nullable=True, comment="结束时间")
    task_total = Column(Integer, nullable=False, default=0, comment="任务总数")
    task_success = Column(Integer, nullable=False, default=0, comment="成功任务数")
    task_failed = Column(Integer, nullable=False, default=0, comment="失败任务数")
    error_message = Column(Text, nullable=True, comment="错误信息")


class DatahubJobTask(BaseModel):
    __tablename__ = "datahub_job_tasks"
    __table_args__ = (
        Index("idx_datahub_job_tasks_run_id", "job_run_id"),
        Index("idx_datahub_job_tasks_dataset_symbol", "dataset", "symbol"),
        Index("idx_datahub_job_tasks_status", "status"),
        {"comment": "DataHub 作业子任务记录"},
    )

    job_run_id = Column(String(36), ForeignKey("datahub_job_runs.id", ondelete="CASCADE"), nullable=False, comment="作业ID")
    dataset = Column(String(100), nullable=False, comment="数据集")
    symbol = Column(String(32), nullable=True, comment="证券代码")
    start_date = Column(Date, nullable=True, comment="任务起始日期")
    end_date = Column(Date, nullable=True, comment="任务结束日期")
    status = Column(String(20), nullable=False, default="pending", comment="状态")
    attempts = Column(Integer, nullable=False, default=0, comment="重试次数")
    last_error = Column(Text, nullable=True, comment="最后错误")
    locked_at = Column(DateTime(timezone=True), nullable=True, comment="锁定时间")
