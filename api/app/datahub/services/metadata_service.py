from sqlalchemy.orm import Session

from app.datahub.catalog import ALL_DATASETS
from app.datahub.models import DatahubDatasetCatalog


class DatahubMetadataService:
    """DataHub 元数据服务（第一阶段：目录初始化）。"""

    def __init__(self, db: Session):
        self.db = db

    def seed_dataset_catalog(self) -> int:
        created = 0
        existing = {
            row.dataset_key for row in self.db.query(DatahubDatasetCatalog.dataset_key).all()
        }
        for dataset in ALL_DATASETS:
            if dataset in existing:
                continue
            row = DatahubDatasetCatalog(
                dataset_key=dataset,
                layer="normalized",
                schema_version="1.0",
                primary_keys=["dataset", "symbol", "trade_date"],
                partition_by=["year", "month"],
                is_active="true",
            )
            self.db.add(row)
            created += 1
        if created > 0:
            self.db.commit()
        return created
