from sqlalchemy import Column, Date, Float, Index, JSON, String, Text, UniqueConstraint

from app.common.models.base_model import BaseModel


class DatahubDatasetCatalog(BaseModel):
    __tablename__ = "datahub_dataset_catalog"
    __table_args__ = (
        UniqueConstraint("dataset_key", name="uq_datahub_dataset_catalog_dataset_key"),
        {"comment": "DataHub 数据集目录与口径元信息"},
    )

    dataset_key = Column(String(100), nullable=False, comment="数据集唯一键")
    layer = Column(String(20), nullable=False, comment="数据层：raw/normalized/features")
    schema_version = Column(String(20), nullable=False, default="1.0", comment="Schema 版本")
    primary_keys = Column(JSON, nullable=True, comment="主键定义")
    partition_by = Column(JSON, nullable=True, comment="分区字段")
    description = Column(Text, nullable=True, comment="说明")
    is_active = Column(String(10), nullable=False, default="true", comment="是否启用")


class DatahubDatasetWatermark(BaseModel):
    __tablename__ = "datahub_dataset_watermarks"
    __table_args__ = (
        UniqueConstraint("dataset", "symbol", name="uq_datahub_dataset_watermarks_dataset_symbol"),
        Index("idx_datahub_dataset_watermarks_dataset", "dataset"),
        {"comment": "DataHub 数据集增量水位"},
    )

    dataset = Column(String(100), nullable=False, comment="数据集")
    symbol = Column(String(32), nullable=True, comment="证券代码")
    last_success_date = Column(Date, nullable=True, comment="最近成功日期")
    last_quality_score = Column(Float, nullable=True, comment="最近质量分")
    last_object_key = Column(String(500), nullable=True, comment="最近对象路径")
    last_batch_id = Column(String(64), nullable=True, comment="最近批次ID")
