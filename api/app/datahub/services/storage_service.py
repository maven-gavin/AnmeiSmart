import hashlib
import json
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.datahub.models import DatahubObjectIndex
from app.datahub.storage import MinioParquetStore


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

    def publish_latest_manifest(
        self,
        *,
        dataset: str,
        symbol: str | None,
        object_key: str,
        schema_version: str,
        quality_score: float,
        start_date: date | None,
        end_date: date | None,
    ) -> str:
        symbol_part = symbol or "__ALL__"
        manifest_key = f"datahub/normalized/dataset={dataset}/latest/symbol={symbol_part}.json"
        payload = {
            "dataset": dataset,
            "symbol": symbol,
            "object_key": object_key,
            "schema_version": schema_version,
            "quality_score": quality_score,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        }
        MinioParquetStore().put_bytes(
            object_key=manifest_key,
            data=json.dumps(payload, ensure_ascii=True).encode("utf-8"),
            content_type="application/json",
        )
        return manifest_key
