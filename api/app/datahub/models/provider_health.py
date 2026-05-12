from sqlalchemy import Column, DateTime, Index, Integer, String, Text, UniqueConstraint

from app.common.models.base_model import BaseModel


class DatahubProviderHealth(BaseModel):
    __tablename__ = "datahub_provider_health"
    __table_args__ = (
        UniqueConstraint("provider", "dataset", name="uq_datahub_provider_health_provider_dataset"),
        Index("idx_datahub_provider_health_status", "status"),
        {"comment": "DataHub Provider 健康状态"},
    )

    provider = Column(String(50), nullable=False, comment="数据源标识")
    dataset = Column(String(100), nullable=False, comment="数据集")
    status = Column(String(20), nullable=False, default="healthy", comment="健康状态")
    success_count = Column(Integer, nullable=False, default=0, comment="成功次数")
    failure_count = Column(Integer, nullable=False, default=0, comment="失败次数")
    last_success_at = Column(DateTime(timezone=True), nullable=True, comment="最近成功时间")
    last_failure_at = Column(DateTime(timezone=True), nullable=True, comment="最近失败时间")
    last_error = Column(Text, nullable=True, comment="最近错误")
    cooldown_until = Column(DateTime(timezone=True), nullable=True, comment="冷却到期时间")
