from sqlalchemy import Column, Date, Float, Index, Integer, String, UniqueConstraint

from app.common.models.base_model import BaseModel


class DatahubObjectIndex(BaseModel):
    __tablename__ = "datahub_object_index"
    __table_args__ = (
        UniqueConstraint("bucket", "object_key", name="uq_datahub_object_index_bucket_object_key"),
        Index("idx_datahub_object_index_dataset_layer", "dataset", "layer"),
        Index("idx_datahub_object_index_symbol_date", "symbol", "start_date", "end_date"),
        {"comment": "DataHub MinIO 对象索引"},
    )

    bucket = Column(String(128), nullable=False, comment="MinIO bucket")
    object_key = Column(String(500), nullable=False, comment="对象路径")
    dataset = Column(String(100), nullable=False, comment="数据集")
    layer = Column(String(20), nullable=False, comment="层级")
    provider = Column(String(50), nullable=True, comment="来源数据源")
    symbol = Column(String(32), nullable=True, comment="证券代码")
    start_date = Column(Date, nullable=True, comment="覆盖起始日期")
    end_date = Column(Date, nullable=True, comment="覆盖结束日期")
    row_count = Column(Integer, nullable=False, default=0, comment="行数")
    schema_version = Column(String(20), nullable=False, default="1.0", comment="Schema 版本")
    content_hash = Column(String(128), nullable=True, comment="内容哈希")
    quality_score = Column(Float, nullable=True, comment="质量分")
