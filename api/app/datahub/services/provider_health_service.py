from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.datahub.models import DatahubProviderHealth


class DatahubProviderHealthService:
    """Provider 健康状态与简易熔断服务。"""

    FAILURE_SAMPLE_THRESHOLD = 20
    FAILURE_RATE_THRESHOLD = 0.5
    COOLDOWN_SECONDS = 30

    def __init__(self, db: Session):
        self.db = db

    def is_available(self, *, provider: str, dataset: str) -> bool:
        row = self._get(provider=provider, dataset=dataset)
        if row is None:
            return True
        if row.cooldown_until is None:
            return True
        return row.cooldown_until <= datetime.now(timezone.utc)

    def record_success(self, *, provider: str, dataset: str) -> None:
        now = datetime.now(timezone.utc)
        row = self._get_or_create(provider=provider, dataset=dataset)
        row.success_count = row.success_count + 1
        row.status = "healthy"
        row.last_success_at = now
        row.last_error = None
        row.cooldown_until = None
        self.db.commit()

    def record_failure(self, *, provider: str, dataset: str, error: str) -> None:
        now = datetime.now(timezone.utc)
        row = self._get_or_create(provider=provider, dataset=dataset)
        row.failure_count = row.failure_count + 1
        row.last_failure_at = now
        row.last_error = error[:2000]

        total = row.success_count + row.failure_count
        failure_rate = (row.failure_count / total) if total > 0 else 1.0
        should_open_circuit = total >= self.FAILURE_SAMPLE_THRESHOLD and failure_rate > self.FAILURE_RATE_THRESHOLD

        if should_open_circuit:
            row.status = "cooldown"
            row.cooldown_until = now + timedelta(seconds=self.COOLDOWN_SECONDS)
        else:
            row.status = "degraded"
        self.db.commit()

    def _get_or_create(self, *, provider: str, dataset: str) -> DatahubProviderHealth:
        row = self._get(provider=provider, dataset=dataset)
        if row is not None:
            return row
        row = DatahubProviderHealth(provider=provider, dataset=dataset, status="healthy")
        self.db.add(row)
        self.db.flush()
        return row

    def _get(self, *, provider: str, dataset: str) -> DatahubProviderHealth | None:
        return (
            self.db.query(DatahubProviderHealth)
            .filter(
                DatahubProviderHealth.provider == provider,
                DatahubProviderHealth.dataset == dataset,
            )
            .first()
        )
