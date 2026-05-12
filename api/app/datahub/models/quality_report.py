from sqlalchemy import Column, Date, DateTime, Float, Index, JSON, String

from app.common.models.base_model import BaseModel


class DatahubQualityReport(BaseModel):
    __tablename__ = "datahub_quality_reports"
    __table_args__ = (
        Index("idx_datahub_quality_reports_dataset_symbol", "dataset", "symbol"),
        Index("idx_datahub_quality_reports_checked_at", "checked_at"),
        {"comment": "DataHub 数据质量报告"},
    )

    dataset = Column(String(100), nullable=False, comment="数据集")
    symbol = Column(String(32), nullable=True, comment="证券代码")
    biz_date = Column(Date, nullable=True, comment="业务日期")
    quality_score = Column(Float, nullable=False, default=0, comment="质量分")
    severity = Column(String(10), nullable=False, default="p2", comment="问题等级")
    issues = Column(JSON, nullable=True, comment="问题详情")
    object_key = Column(String(500), nullable=True, comment="关联对象路径")
    checked_at = Column(DateTime(timezone=True), nullable=False, comment="检查时间")
