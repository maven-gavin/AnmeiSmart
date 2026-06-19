from sqlalchemy.orm import Session

from app.datahub.catalog import ALL_DATASETS, get_dataset_label
from app.datahub.models import DatahubDatasetCatalog


class DatahubMetadataService:
    """DataHub 元数据服务（第一阶段：目录初始化）。"""

    def __init__(self, db: Session):
        self.db = db

    def seed_dataset_catalog(self) -> int:
        created = 0
        existing_rows = {
            row.dataset_key: row for row in self.db.query(DatahubDatasetCatalog).all()
        }
        for dataset in ALL_DATASETS:
            label = get_dataset_label(dataset)
            description = f"{label} ({dataset})"
            if dataset in existing_rows:
                row = existing_rows[dataset]
                if row.description != description:
                    row.description = description
                continue
            row = DatahubDatasetCatalog(
                dataset_key=dataset,
                layer="normalized",
                schema_version="1.0",
                primary_keys=["dataset", "symbol", "trade_date"],
                partition_by=["year", "month"],
                description=description,
                is_active="true",
            )
            self.db.add(row)
            created += 1
        self.db.commit()
        return created
