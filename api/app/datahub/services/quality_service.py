from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.datahub.models import DatahubQualityReport


class DatahubQualityService:
    def __init__(self, db: Session):
        self.db = db

    def write_report(
        self,
        *,
        dataset: str,
        symbol: Optional[str],
        quality_score: float,
        severity: str,
        issues: Optional[list[dict[str, Any]]] = None,
        object_key: Optional[str] = None,
    ) -> DatahubQualityReport:
        row = DatahubQualityReport(
            dataset=dataset,
            symbol=symbol,
            quality_score=quality_score,
            severity=severity,
            issues=issues or [],
            object_key=object_key,
            checked_at=datetime.now(timezone.utc),
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row
