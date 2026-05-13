from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.api import BusinessException, ErrorCode
from app.core.config import get_settings
from app.datahub.enums import DatahubTaskStatus
from app.datahub.models import DatahubObjectIndex
from app.datahub.models import DatahubDatasetWatermark, DatahubJobRun, DatahubJobTask
from app.datahub.providers import BaoStockProvider
from app.datahub.schemas.datahub import TriggerBackfillRequest, TriggerDailyIncrementalRequest
from app.datahub.services.market_daily_backfill_service import MarketDailyBackfillService
from app.datahub.services.provider_health_service import DatahubProviderHealthService
from app.datahub.services.quality_service import DatahubQualityService
from app.datahub.services.router_service import DatahubRouterService
from app.datahub.services.storage_service import DatahubStorageService
from app.datahub.storage import MinioParquetStore


class TradingCalendarSyncService:
    def __init__(self, db: Session):
        self.db = db
        self.provider = BaoStockProvider()
        self.storage_service = DatahubStorageService(db)
        self.quality_service = DatahubQualityService(db)
        self.provider_health_service = DatahubProviderHealthService(db)
        self.router_service = DatahubRouterService()

    def execute_backfill(self, run_id: str, payload: TriggerBackfillRequest) -> None:
        run = self._require_run(run_id)
        task = self._require_or_create_single_task(run_id, start_date=payload.start_date, end_date=payload.end_date)
        self._run_single(run, task, start_date=payload.start_date, end_date=payload.end_date, batch_prefix="backfill")

    def execute_daily_incremental(self, run_id: str, payload: TriggerDailyIncrementalRequest) -> None:
        run = self._require_run(run_id)
        end_date = date.today()
        start_date = end_date - timedelta(days=payload.window_days)
        task = self._require_or_create_single_task(run_id, start_date=start_date, end_date=end_date)
        self._run_single(run, task, start_date=start_date, end_date=end_date, batch_prefix="daily")

    def _run_single(self, run: DatahubJobRun, task: DatahubJobTask, *, start_date: date, end_date: date, batch_prefix: str) -> None:
        self._mark_running(run, task)
        try:
            provider_name = self.provider.provider_name
            if not self.provider_health_service.is_available(provider=provider_name, dataset="trading_calendar"):
                raise BusinessException(
                    f"{provider_name} 当前处于熔断冷却中，请稍后重试",
                    code=ErrorCode.BUSINESS_ERROR,
                )
            try:
                rows = self.router_service.run_with_policy(
                    dataset="trading_calendar",
                    provider=provider_name,
                    operation=lambda: self.provider.get_trading_calendar(start_date, end_date),
                )
            except Exception as exc:
                self.provider_health_service.record_failure(
                    provider=provider_name,
                    dataset="trading_calendar",
                    error=str(exc),
                )
                raise
            self.provider_health_service.record_success(provider=provider_name, dataset="trading_calendar")
            if not rows:
                raise BusinessException("trading_calendar 未获取到数据", code=ErrorCode.BUSINESS_ERROR)
            parquet_bytes = MarketDailyBackfillService._to_parquet_bytes(rows)
            object_key = (
                "datahub/normalized/"
                f"dataset=trading_calendar/year={end_date.year}/month={end_date.month:02d}/"
                f"batch_id={batch_prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.parquet"
            )
            MinioParquetStore().put_bytes(object_key=object_key, data=parquet_bytes, content_type="application/octet-stream")

            missing_trade_date = sum(1 for row in rows if not row.get("trade_date"))
            score = max(0.0, 100.0 - (missing_trade_date / max(len(rows), 1)) * 100.0)
            severity = "p0" if missing_trade_date > max(1, int(len(rows) * 0.1)) else ("p1" if missing_trade_date > 0 else "p2")
            issues = [{"rule": "trade_date_required", "count": missing_trade_date}] if missing_trade_date > 0 else []

            self.storage_service.upsert_object_index(
                bucket=get_settings().MINIO_BUCKET_NAME,
                object_key=object_key,
                dataset="trading_calendar",
                layer="normalized",
                provider="baostock",
                start_date=start_date,
                end_date=end_date,
                row_count=len(rows),
                schema_version="1.0",
                quality_score=score,
            )
            self.quality_service.write_report(
                dataset="trading_calendar",
                symbol="SSE",
                quality_score=score,
                severity=severity,
                issues=issues,
                object_key=object_key,
            )
            can_publish = self.quality_service.can_publish_latest("trading_calendar", score)
            if can_publish:
                self.storage_service.publish_latest_manifest(
                    dataset="trading_calendar",
                    symbol="SSE",
                    object_key=object_key,
                    schema_version="1.0",
                    quality_score=score,
                    start_date=start_date,
                    end_date=end_date,
                )
                self._upsert_watermark(last_date=end_date, quality_score=score, object_key=object_key, batch_prefix=batch_prefix)
            self._mark_success(run, task)
        except Exception as exc:
            snapshot = self._get_stable_snapshot(required_end_date=end_date)
            if snapshot is not None:
                score, object_key, snapshot_date = snapshot
                self.quality_service.write_report(
                    dataset="trading_calendar",
                    symbol="SSE",
                    quality_score=score,
                    severity="p1",
                    issues=[
                        {
                            "rule": "provider_fallback_snapshot",
                            "message": "trading_calendar 源站失败，降级使用 MinIO 稳定快照",
                            "snapshot_date": snapshot_date.isoformat(),
                        }
                    ],
                    object_key=object_key,
                )
                self._mark_success(run, task)
                return
            self._mark_failed(run, task, str(exc))
            raise

    def _upsert_watermark(self, *, last_date: date, quality_score: float, object_key: str, batch_prefix: str) -> None:
        row = (
            self.db.query(DatahubDatasetWatermark)
            .filter(DatahubDatasetWatermark.dataset == "trading_calendar", DatahubDatasetWatermark.symbol == "SSE")
            .first()
        )
        if row is None:
            row = DatahubDatasetWatermark(dataset="trading_calendar", symbol="SSE")
            self.db.add(row)
        row.last_success_date = last_date
        row.last_quality_score = quality_score
        row.last_object_key = object_key
        row.last_batch_id = f"{batch_prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        self.db.commit()

    def _get_stable_snapshot(self, *, required_end_date: date) -> tuple[float, str, date] | None:
        watermark = (
            self.db.query(DatahubDatasetWatermark)
            .filter(DatahubDatasetWatermark.dataset == "trading_calendar", DatahubDatasetWatermark.symbol == "SSE")
            .first()
        )
        if (
            watermark is None
            or not watermark.last_object_key
            or watermark.last_success_date is None
            or watermark.last_quality_score is None
        ):
            return None
        if watermark.last_quality_score < 95:
            return None
        if watermark.last_success_date < required_end_date:
            return None
        if not MinioParquetStore().exists(watermark.last_object_key):
            return None
        indexed = (
            self.db.query(DatahubObjectIndex.id)
            .filter(DatahubObjectIndex.object_key == watermark.last_object_key)
            .first()
        )
        if indexed is None:
            return None
        return (
            float(watermark.last_quality_score),
            watermark.last_object_key,
            watermark.last_success_date,
        )

    def _require_run(self, run_id: str) -> DatahubJobRun:
        row = self.db.query(DatahubJobRun).filter(DatahubJobRun.id == run_id).first()
        if row is None:
            raise BusinessException("作业不存在", code=ErrorCode.NOT_FOUND)
        return row

    def _require_or_create_single_task(self, run_id: str, *, start_date: date, end_date: date) -> DatahubJobTask:
        row = self.db.query(DatahubJobTask).filter(DatahubJobTask.job_run_id == run_id).first()
        if row is not None:
            return row
        row = DatahubJobTask(
            job_run_id=run_id,
            dataset="trading_calendar",
            symbol="SSE",
            start_date=start_date,
            end_date=end_date,
            status=DatahubTaskStatus.PENDING.value,
            attempts=0,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def _mark_running(self, run: DatahubJobRun, task: DatahubJobTask) -> None:
        run.status = DatahubTaskStatus.RUNNING.value
        run.started_at = datetime.now(timezone.utc)
        run.task_total = 1
        task.status = DatahubTaskStatus.RUNNING.value
        task.attempts = task.attempts + 1
        task.locked_at = datetime.now(timezone.utc)
        self.db.commit()

    def _mark_success(self, run: DatahubJobRun, task: DatahubJobTask) -> None:
        run.status = DatahubTaskStatus.SUCCESS.value
        run.task_success = 1
        run.task_failed = 0
        run.finished_at = datetime.now(timezone.utc)
        run.error_message = None
        task.status = DatahubTaskStatus.SUCCESS.value
        task.last_error = None
        self.db.commit()

    def _mark_failed(self, run: DatahubJobRun, task: DatahubJobTask, message: str) -> None:
        run.status = DatahubTaskStatus.FAILED.value
        run.task_success = 0
        run.task_failed = 1
        run.finished_at = datetime.now(timezone.utc)
        run.error_message = message[:2000]
        task.status = DatahubTaskStatus.FAILED.value
        task.last_error = message[:2000]
        self.db.commit()
