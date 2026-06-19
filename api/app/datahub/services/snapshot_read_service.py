from __future__ import annotations

import json
from datetime import date, datetime
from io import BytesIO
from typing import Any

from sqlalchemy.orm import Session

from app.datahub.models import DatahubDatasetWatermark, DatahubObjectIndex
from app.datahub.storage import MinioParquetStore


class SnapshotDatasetReadService:
    """从 MinIO 读取全量快照类数据集（security_master、sector_members 等）。"""

    def __init__(self, db: Session, dataset: str):
        self.db = db
        self.dataset = dataset
        self.store = MinioParquetStore()

    def load_rows(self) -> list[dict[str, Any]]:
        object_key = self._resolve_object_key()
        if not object_key:
            return []
        return self._read_parquet_rows(object_key)

    def _resolve_object_key(self) -> str | None:
        manifest_key = f"datahub/normalized/dataset={self.dataset}/latest/symbol=__ALL__.json"
        if self.store.exists(manifest_key):
            payload = json.loads(self.store.get_bytes(manifest_key).decode("utf-8"))
            object_key = payload.get("object_key")
            if object_key and self.store.exists(object_key):
                return str(object_key)

        watermark = (
            self.db.query(DatahubDatasetWatermark)
            .filter(
                DatahubDatasetWatermark.dataset == self.dataset,
                DatahubDatasetWatermark.symbol.is_(None),
            )
            .first()
        )
        if watermark and watermark.last_object_key and self.store.exists(watermark.last_object_key):
            return watermark.last_object_key

        indexed = (
            self.db.query(DatahubObjectIndex)
            .filter(
                DatahubObjectIndex.dataset == self.dataset,
                DatahubObjectIndex.symbol.is_(None),
            )
            .order_by(DatahubObjectIndex.end_date.desc().nullslast(), DatahubObjectIndex.created_at.desc())
            .first()
        )
        if indexed and self.store.exists(indexed.object_key):
            return indexed.object_key
        return None

    @staticmethod
    def _read_parquet_rows(object_key: str) -> list[dict[str, Any]]:
        import pyarrow.parquet as pq

        raw = MinioParquetStore().get_bytes(object_key)
        table = pq.read_table(BytesIO(raw))
        return table.to_pylist()

    @staticmethod
    def _to_date(value: Any) -> date | None:
        if value is None:
            return None
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            return datetime.strptime(value[:10], "%Y-%m-%d").date()
        return None
