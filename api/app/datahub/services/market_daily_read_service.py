from __future__ import annotations

import json
from datetime import date, datetime
from io import BytesIO
from typing import Any

from sqlalchemy.orm import Session

from app.datahub.models import DatahubDatasetWatermark, DatahubObjectIndex
from app.datahub.normalize import normalize_symbol
from app.datahub.storage import MinioParquetStore


class MarketDailyReadService:
    """从 MinIO 标准层读取 market_daily 日线数据。"""

    def __init__(self, db: Session):
        self.db = db
        self.store = MinioParquetStore()

    def get_bars(self, *, symbol: str, start_date: date, end_date: date) -> list[dict[str, Any]]:
        normalized = normalize_symbol(symbol)
        object_key = self._resolve_object_key(normalized)
        if not object_key:
            return []

        rows = self._read_parquet_rows(object_key)
        filtered: list[dict[str, Any]] = []
        for row in rows:
            trade_date = self._to_date(row.get("trade_date"))
            if trade_date is None:
                continue
            if trade_date < start_date or trade_date > end_date:
                continue
            filtered.append(self._normalize_bar_row(row, normalized, trade_date))

        filtered.sort(key=lambda item: item["trade_date"])
        return filtered

    def get_latest_bar(self, *, symbol: str) -> dict[str, Any] | None:
        normalized = normalize_symbol(symbol)
        object_key = self._resolve_object_key(normalized)
        if not object_key:
            return None

        rows = self._read_parquet_rows(object_key)
        latest: dict[str, Any] | None = None
        latest_date: date | None = None
        for row in rows:
            trade_date = self._to_date(row.get("trade_date"))
            if trade_date is None:
                continue
            if latest_date is None or trade_date > latest_date:
                latest_date = trade_date
                latest = self._normalize_bar_row(row, normalized, trade_date)
        return latest

    def _resolve_object_key(self, symbol: str) -> str | None:
        manifest_key = f"datahub/normalized/dataset=market_daily/latest/symbol={symbol}.json"
        if self.store.exists(manifest_key):
            payload = json.loads(self.store.get_bytes(manifest_key).decode("utf-8"))
            object_key = payload.get("object_key")
            if object_key and self.store.exists(object_key):
                return str(object_key)

        watermark = (
            self.db.query(DatahubDatasetWatermark)
            .filter(
                DatahubDatasetWatermark.dataset == "market_daily",
                DatahubDatasetWatermark.symbol == symbol,
            )
            .first()
        )
        if watermark and watermark.last_object_key and self.store.exists(watermark.last_object_key):
            return watermark.last_object_key

        indexed = (
            self.db.query(DatahubObjectIndex)
            .filter(
                DatahubObjectIndex.dataset == "market_daily",
                DatahubObjectIndex.symbol == symbol,
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

    @staticmethod
    def _normalize_bar_row(row: dict[str, Any], symbol: str, trade_date: date) -> dict[str, Any]:
        return {
            "symbol": symbol,
            "trade_date": trade_date,
            "open": float(row.get("open") or 0),
            "high": float(row.get("high") or 0),
            "low": float(row.get("low") or 0),
            "close": float(row.get("close") or 0),
            "volume": float(row.get("volume") or 0),
            "amount": float(row.get("amount") or 0),
            "turnover_rate": float(row.get("turnover_rate") or 0) if row.get("turnover_rate") not in (None, "") else None,
        }
