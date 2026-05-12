from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.datahub.models import (
    DatahubDatasetCatalog,
    DatahubJobRun,
    DatahubJobTask,
    DatahubObjectIndex,
    DatahubQualityReport,
    DatahubWorkerHeartbeat,
)
from app.datahub.schemas.datahub import (
    DatahubDatasetInfo,
    DatahubJobTaskInfo,
    DatahubJobRunInfo,
    DatahubObjectIndexInfo,
    DatahubQualityReportInfo,
    DatahubWorkerHeartbeatInfo,
    TriggerBackfillRequest,
    TriggerDailyIncrementalRequest,
)
from app.datahub.enums import DatahubTaskStatus


class DatahubService:
    def __init__(self, db: Session):
        self.db = db

    def list_datasets(self) -> list[DatahubDatasetInfo]:
        rows = (
            self.db.query(DatahubDatasetCatalog)
            .order_by(DatahubDatasetCatalog.dataset_key.asc())
            .all()
        )
        return [
            DatahubDatasetInfo(
                id=row.id,
                dataset_key=row.dataset_key,
                layer=row.layer,
                schema_version=row.schema_version,
                description=row.description,
                is_active=row.is_active,
                updated_at=row.updated_at,
            )
            for row in rows
        ]

    def get_job_run(self, run_id: str) -> DatahubJobRunInfo | None:
        row = self.db.query(DatahubJobRun).filter(DatahubJobRun.id == run_id).first()
        if row is None:
            return None
        return self._to_job_info(row)

    def list_job_tasks(self, run_id: str) -> list[DatahubJobTaskInfo]:
        rows = (
            self.db.query(DatahubJobTask)
            .filter(DatahubJobTask.job_run_id == run_id)
            .order_by(DatahubJobTask.created_at.asc())
            .all()
        )
        return [
            DatahubJobTaskInfo(
                id=row.id,
                job_run_id=row.job_run_id,
                dataset=row.dataset,
                symbol=row.symbol,
                start_date=row.start_date,
                end_date=row.end_date,
                status=row.status,
                attempts=row.attempts,
                last_error=row.last_error,
                locked_at=row.locked_at,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in rows
        ]

    def list_quality_reports(
        self,
        *,
        dataset: str | None = None,
        symbol: str | None = None,
        limit: int = 100,
    ) -> list[DatahubQualityReportInfo]:
        query = self.db.query(DatahubQualityReport)
        if dataset:
            query = query.filter(DatahubQualityReport.dataset == dataset)
        if symbol:
            query = query.filter(DatahubQualityReport.symbol == symbol)
        rows = query.order_by(DatahubQualityReport.checked_at.desc()).limit(limit).all()
        return [
            DatahubQualityReportInfo(
                id=row.id,
                dataset=row.dataset,
                symbol=row.symbol,
                biz_date=row.biz_date,
                quality_score=row.quality_score,
                severity=row.severity,
                issues=row.issues,
                object_key=row.object_key,
                checked_at=row.checked_at,
                created_at=row.created_at,
            )
            for row in rows
        ]

    def list_object_indexes(
        self,
        *,
        dataset: str | None = None,
        symbol: str | None = None,
        limit: int = 100,
    ) -> list[DatahubObjectIndexInfo]:
        query = self.db.query(DatahubObjectIndex)
        if dataset:
            query = query.filter(DatahubObjectIndex.dataset == dataset)
        if symbol:
            query = query.filter(DatahubObjectIndex.symbol == symbol)
        rows = query.order_by(DatahubObjectIndex.created_at.desc()).limit(limit).all()
        return [
            DatahubObjectIndexInfo(
                id=row.id,
                bucket=row.bucket,
                object_key=row.object_key,
                dataset=row.dataset,
                layer=row.layer,
                provider=row.provider,
                symbol=row.symbol,
                start_date=row.start_date,
                end_date=row.end_date,
                row_count=row.row_count,
                schema_version=row.schema_version,
                content_hash=row.content_hash,
                quality_score=row.quality_score,
                created_at=row.created_at,
            )
            for row in rows
        ]

    def list_job_runs(self, limit: int = 20) -> list[DatahubJobRunInfo]:
        rows = (
            self.db.query(DatahubJobRun)
            .order_by(DatahubJobRun.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            DatahubJobRunInfo(
                id=row.id,
                job_type=row.job_type,
                dataset=row.dataset,
                status=row.status,
                trigger_source=row.trigger_source,
                started_at=row.started_at,
                finished_at=row.finished_at,
                task_total=row.task_total,
                task_success=row.task_success,
                task_failed=row.task_failed,
                error_message=row.error_message,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in rows
        ]

    def upsert_worker_heartbeat(
        self,
        *,
        worker_name: str,
        status: str,
        last_run_id: str | None = None,
        increment_processed: bool = False,
        last_error: str | None = None,
    ) -> None:
        row = self.db.query(DatahubWorkerHeartbeat).filter(DatahubWorkerHeartbeat.worker_name == worker_name).first()
        if row is None:
            row = DatahubWorkerHeartbeat(
                worker_name=worker_name,
                status=status,
                last_heartbeat_at=datetime.now(timezone.utc),
                last_run_id=last_run_id,
                processed_count=1 if increment_processed else 0,
                last_error=last_error,
            )
            self.db.add(row)
            self.db.commit()
            return

        row.status = status
        row.last_heartbeat_at = datetime.now(timezone.utc)
        row.last_run_id = last_run_id or row.last_run_id
        if increment_processed:
            row.processed_count = row.processed_count + 1
        row.last_error = last_error
        self.db.commit()

    def get_worker_heartbeat(
        self,
        worker_name: str = "datahub-default-worker",
        offline_threshold_seconds: int = 30,
    ) -> DatahubWorkerHeartbeatInfo | None:
        row = (
            self.db.query(DatahubWorkerHeartbeat)
            .filter(DatahubWorkerHeartbeat.worker_name == worker_name)
            .first()
        )
        if row is None:
            return None
        now = datetime.now(timezone.utc)
        is_online = row.last_heartbeat_at >= now - timedelta(seconds=offline_threshold_seconds)
        return DatahubWorkerHeartbeatInfo(
            worker_name=row.worker_name,
            status=row.status,
            last_heartbeat_at=row.last_heartbeat_at,
            last_run_id=row.last_run_id,
            processed_count=row.processed_count,
            last_error=row.last_error,
            is_online=is_online,
            offline_threshold_seconds=offline_threshold_seconds,
        )

    def create_backfill_job(self, payload: TriggerBackfillRequest, trigger_source: str = "api") -> DatahubJobRunInfo:
        job_run = DatahubJobRun(
            job_type="backfill",
            dataset=payload.dataset,
            status=DatahubTaskStatus.PENDING.value,
            trigger_source=trigger_source,
            job_params=payload.model_dump(mode="json"),
            started_at=None,
            task_total=1,
            task_success=0,
            task_failed=0,
        )
        self.db.add(job_run)
        self.db.flush()

        task = DatahubJobTask(
            job_run_id=job_run.id,
            dataset=payload.dataset,
            symbol=payload.symbol,
            start_date=payload.start_date,
            end_date=payload.end_date,
            status=DatahubTaskStatus.PENDING.value,
            attempts=0,
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(job_run)
        return self._to_job_info(job_run)

    def create_daily_incremental_job(
        self,
        payload: TriggerDailyIncrementalRequest,
        trigger_source: str = "api",
    ) -> DatahubJobRunInfo:
        job_run = DatahubJobRun(
            job_type="daily_incremental",
            dataset=payload.dataset,
            status=DatahubTaskStatus.PENDING.value,
            trigger_source=trigger_source,
            job_params=payload.model_dump(mode="json"),
            started_at=None,
            task_total=0,
            task_success=0,
            task_failed=0,
        )
        self.db.add(job_run)
        self.db.commit()
        self.db.refresh(job_run)
        return self._to_job_info(job_run)

    def mark_run_failed(self, run_id: str, message: str) -> None:
        row = self.db.query(DatahubJobRun).filter(DatahubJobRun.id == run_id).first()
        if row is None:
            return
        row.status = DatahubTaskStatus.FAILED.value
        row.error_message = message[:2000]
        row.finished_at = datetime.now(timezone.utc)
        self.db.commit()

    def list_pending_run_ids(self, limit: int = 10) -> list[str]:
        rows = (
            self.db.query(DatahubJobRun.id)
            .filter(DatahubJobRun.status == DatahubTaskStatus.PENDING.value)
            .order_by(DatahubJobRun.created_at.asc())
            .limit(limit)
            .all()
        )
        return [row.id for row in rows]

    @staticmethod
    def _to_job_info(row: DatahubJobRun) -> DatahubJobRunInfo:
        return DatahubJobRunInfo(
            id=row.id,
            job_type=row.job_type,
            dataset=row.dataset,
            status=row.status,
            trigger_source=row.trigger_source,
            started_at=row.started_at,
            finished_at=row.finished_at,
            task_total=row.task_total,
            task_success=row.task_success,
            task_failed=row.task_failed,
            error_message=row.error_message,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
