from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.api import BusinessException, ErrorCode
from app.core.config import get_settings
from app.datahub.enums import DatahubTaskStatus
from app.datahub.models import DatahubDatasetWatermark, DatahubJobRun, DatahubJobTask
from app.datahub.providers import BaoStockProvider
from app.datahub.schemas.datahub import TriggerBackfillRequest, TriggerDailyIncrementalRequest
from app.datahub.services.market_daily_backfill_service import MarketDailyBackfillService
from app.datahub.services.quality_service import DatahubQualityService
from app.datahub.services.storage_service import DatahubStorageService
from app.datahub.storage import MinioParquetStore


class SecurityMasterSyncService:
    def __init__(self, db: Session):
        self.db = db
        self.provider = BaoStockProvider()
        self.storage_service = DatahubStorageService(db)
        self.quality_service = DatahubQualityService(db)

    def execute_backfill(self, run_id: str, payload: TriggerBackfillRequest) -> None:
        run = self._require_run(run_id)
        task = self._require_or_create_single_task(run_id, start_date=payload.start_date, end_date=payload.end_date)
        self._run_single(run, task, batch_prefix="backfill")

    def execute_daily_incremental(self, run_id: str, payload: TriggerDailyIncrementalRequest) -> None:
        run = self._require_run(run_id)
        today = date.today()
        task = self._require_or_create_single_task(run_id, start_date=today, end_date=today)
        self._run_single(run, task, batch_prefix="daily")

    def _run_single(self, run: DatahubJobRun, task: DatahubJobTask, *, batch_prefix: str) -> None:
        self._mark_running(run, task)
        try:
            rows, biz_date = self._load_security_master_rows()
            if not rows:
                raise BusinessException("security_master 未获取到数据", code=ErrorCode.BUSINESS_ERROR)
            parquet_bytes = MarketDailyBackfillService._to_parquet_bytes(rows)
            object_key = (
                "datahub/normalized/"
                f"dataset=security_master/year={biz_date.year}/month={biz_date.month:02d}/"
                f"batch_id={batch_prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.parquet"
            )
            MinioParquetStore().put_bytes(object_key=object_key, data=parquet_bytes, content_type="application/octet-stream")

            missing_symbol = sum(1 for row in rows if not row.get("symbol"))
            missing_name = sum(1 for row in rows if not row.get("name"))
            issue_count = missing_symbol + missing_name
            score = max(0.0, 100.0 - (issue_count / max(len(rows), 1)) * 100.0)
            severity = "p0" if issue_count > max(1, int(len(rows) * 0.1)) else ("p1" if issue_count > 0 else "p2")
            issues = []
            if missing_symbol > 0:
                issues.append({"rule": "symbol_required", "count": missing_symbol})
            if missing_name > 0:
                issues.append({"rule": "name_required", "count": missing_name})

            self.storage_service.upsert_object_index(
                bucket=get_settings().MINIO_BUCKET_NAME,
                object_key=object_key,
                dataset="security_master",
                layer="normalized",
                provider="baostock",
                start_date=biz_date,
                end_date=biz_date,
                row_count=len(rows),
                schema_version="1.0",
            )
            self.quality_service.write_report(
                dataset="security_master",
                symbol=None,
                quality_score=score,
                severity=severity,
                issues=issues,
                object_key=object_key,
            )
            self._upsert_watermark(last_date=biz_date, quality_score=score, object_key=object_key, batch_prefix=batch_prefix)
            self._mark_success(run, task)
        except Exception as exc:
            self._mark_failed(run, task, str(exc))
            raise

    def _load_security_master_rows(self) -> tuple[list[dict], date]:
        today = date.today()
        for offset in range(0, 8):
            query_date = today - timedelta(days=offset)
            rows = self.provider.get_security_master(day=query_date)
            if rows:
                return rows, query_date
        return [], today

    def _upsert_watermark(self, *, last_date: date, quality_score: float, object_key: str, batch_prefix: str) -> None:
        row = (
            self.db.query(DatahubDatasetWatermark)
            .filter(DatahubDatasetWatermark.dataset == "security_master", DatahubDatasetWatermark.symbol.is_(None))
            .first()
        )
        if row is None:
            row = DatahubDatasetWatermark(dataset="security_master", symbol=None)
            self.db.add(row)
        row.last_success_date = last_date
        row.last_quality_score = quality_score
        row.last_object_key = object_key
        row.last_batch_id = f"{batch_prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        self.db.commit()

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
            dataset="security_master",
            symbol=None,
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
