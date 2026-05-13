from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.datahub.models import DatahubQualityReport


class DatahubQualityService:
    CORE_DATASETS = {"market_daily", "security_master", "trading_calendar"}

    def __init__(self, db: Session):
        self.db = db

    @classmethod
    def quality_threshold(cls, dataset: str) -> float:
        return 95.0 if dataset in cls.CORE_DATASETS else 90.0

    @classmethod
    def can_publish_latest(cls, dataset: str, quality_score: float) -> bool:
        return quality_score >= cls.quality_threshold(dataset)

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
