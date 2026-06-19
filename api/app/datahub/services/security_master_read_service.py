from __future__ import annotations

from sqlalchemy.orm import Session

from app.datahub.normalize import normalize_symbol
from app.datahub.services.snapshot_read_service import SnapshotDatasetReadService


class SecurityMasterReadService:
    def __init__(self, db: Session):
        self._reader = SnapshotDatasetReadService(db, "security_master")

    def get_name_map(self) -> dict[str, str]:
        result: dict[str, str] = {}
        for row in self._reader.load_rows():
            symbol = normalize_symbol(str(row.get("symbol") or ""))
            name = str(row.get("name") or "").strip()
            if symbol and name:
                result[symbol] = name
        return result

    def lookup_name(self, symbol: str) -> str | None:
        return self.get_name_map().get(normalize_symbol(symbol))
