import hashlib
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.datahub.models import DatahubObjectIndex


class DatahubStorageService:
    def __init__(self, db: Session):
        self.db = db

    def upsert_object_index(
        self,
        *,
        bucket: str,
        object_key: str,
        dataset: str,
        layer: str,
        provider: Optional[str] = None,
        symbol: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        row_count: int = 0,
        schema_version: str = "1.0",
        content_hash: Optional[str] = None,
        quality_score: Optional[float] = None,
    ) -> DatahubObjectIndex:
        row = (
            self.db.query(DatahubObjectIndex)
            .filter(
                DatahubObjectIndex.bucket == bucket,
                DatahubObjectIndex.object_key == object_key,
            )
            .first()
        )
        if row is None:
            row = DatahubObjectIndex(bucket=bucket, object_key=object_key, dataset=dataset, layer=layer)
            self.db.add(row)

        row.provider = provider
        row.symbol = symbol
        row.start_date = start_date
        row.end_date = end_date
        row.row_count = row_count
        row.schema_version = schema_version
        row.content_hash = content_hash or hashlib.sha256(object_key.encode("utf-8")).hexdigest()
        row.quality_score = quality_score
        self.db.commit()
        self.db.refresh(row)
        return row
