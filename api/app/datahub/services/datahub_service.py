from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.datahub.models import (
    DatahubDatasetCatalog,
    DatahubJobRun,
    DatahubJobTask,
    DatahubObjectIndex,
    DatahubProviderHealth,
    DatahubQualityReport,
    DatahubWorkerHeartbeat,
)
from app.datahub.schemas.datahub import (
    DatahubDatasetInfo,
    DatahubFailureGroupInfo,
    DatahubJobTaskInfo,
    DatahubJobRunInfo,
    DatahubRunFailureDetailInfo,
    FillMarketDailyMissingResult,
    DatahubObjectIndexInfo,
    MarketDailyMissingScanResult,
    RetryFailedTasksResult,
    DatahubQualityReportInfo,
    DatahubProviderHealthInfo,
    DatahubWorkerHeartbeatInfo,
    TriggerBackfillRequest,
    TriggerDailyIncrementalRequest,
)
from app.core.api import BusinessException, ErrorCode
from app.datahub.enums import DatahubTaskStatus
from app.datahub.normalize import normalize_symbol
from app.datahub.providers import BaoStockProvider


class DatahubService:
    SUPPORTED_BACKFILL_DATASETS = {"market_daily", "security_master", "trading_calendar"}
    SUPPORTED_DAILY_DATASETS = {"market_daily", "security_master", "trading_calendar"}

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

    def list_provider_health(
        self,
        *,
        dataset: str | None = None,
        provider: str | None = None,
        limit: int = 100,
    ) -> list[DatahubProviderHealthInfo]:
        query = self.db.query(DatahubProviderHealth)
        if dataset:
            query = query.filter(DatahubProviderHealth.dataset == dataset)
        if provider:
            query = query.filter(DatahubProviderHealth.provider == provider)
        rows = query.order_by(DatahubProviderHealth.updated_at.desc()).limit(limit).all()
        now = datetime.now(timezone.utc)
        items: list[DatahubProviderHealthInfo] = []
        for row in rows:
            total = row.success_count + row.failure_count
            failure_rate = (row.failure_count / total) if total > 0 else 0.0
            is_available = row.cooldown_until is None or row.cooldown_until <= now
            items.append(
                DatahubProviderHealthInfo(
                    provider=row.provider,
                    dataset=row.dataset,
                    status=row.status,
                    success_count=row.success_count,
                    failure_count=row.failure_count,
                    failure_rate=failure_rate,
                    last_success_at=row.last_success_at,
                    last_failure_at=row.last_failure_at,
                    last_error=row.last_error,
                    cooldown_until=row.cooldown_until,
                    is_available=is_available,
                )
            )
        return items

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
        if payload.dataset not in self.SUPPORTED_BACKFILL_DATASETS:
            raise BusinessException(
                f"当前不支持 backfill dataset: {payload.dataset}",
                code=ErrorCode.VALIDATION_ERROR,
            )
        if payload.symbols and payload.dataset != "market_daily":
            raise BusinessException(
                "symbols 仅支持 market_daily 回填",
                code=ErrorCode.VALIDATION_ERROR,
            )
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
            symbol=payload.symbol or ((payload.symbols or [None])[0]),
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
        if payload.dataset not in self.SUPPORTED_DAILY_DATASETS:
            raise BusinessException(
                f"当前不支持 daily_incremental dataset: {payload.dataset}",
                code=ErrorCode.VALIDATION_ERROR,
            )
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

    def delete_job_run(self, run_id: str) -> None:
        row = self.db.query(DatahubJobRun).filter(DatahubJobRun.id == run_id).first()
        if row is None:
            raise BusinessException("作业记录不存在", code=ErrorCode.NOT_FOUND)
        if row.status == DatahubTaskStatus.RUNNING.value:
            raise BusinessException("运行中的作业不可删除，请等待结束后再试", code=ErrorCode.BUSINESS_ERROR)
        self.db.delete(row)
        self.db.commit()

    def purge_job_runs(self, *, status: str, limit: int) -> int:
        if status == DatahubTaskStatus.RUNNING.value:
            raise BusinessException("不支持删除 running 状态的作业批量记录", code=ErrorCode.VALIDATION_ERROR)
        allowed = {s.value for s in DatahubTaskStatus}
        if status not in allowed:
            raise BusinessException(f"无效的 status: {status}", code=ErrorCode.VALIDATION_ERROR)

        rows = (
            self.db.query(DatahubJobRun)
            .filter(DatahubJobRun.status == status)
            .order_by(DatahubJobRun.created_at.asc())
            .limit(limit)
            .all()
        )
        for row in rows:
            self.db.delete(row)
        self.db.commit()
        return len(rows)

    def get_run_failure_detail(self, run_id: str, limit: int = 200) -> DatahubRunFailureDetailInfo:
        run = self.db.query(DatahubJobRun).filter(DatahubJobRun.id == run_id).first()
        if run is None:
            raise BusinessException("作业记录不存在", code=ErrorCode.NOT_FOUND)
        failed_rows = (
            self.db.query(DatahubJobTask)
            .filter(
                DatahubJobTask.job_run_id == run_id,
                DatahubJobTask.status == DatahubTaskStatus.FAILED.value,
            )
            .order_by(DatahubJobTask.updated_at.desc())
            .limit(limit)
            .all()
        )
        grouped: dict[str, list[str]] = defaultdict(list)
        for row in failed_rows:
            key = row.last_error or "未知错误"
            symbol = row.symbol or "-"
            if symbol not in grouped[key]:
                grouped[key].append(symbol)

        groups = [
            DatahubFailureGroupInfo(
                error_message=message,
                count=len(symbols),
                symbols=symbols[:20],
            )
            for message, symbols in sorted(grouped.items(), key=lambda item: len(item[1]), reverse=True)
        ]
        tasks = [
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
            for row in failed_rows
        ]
        return DatahubRunFailureDetailInfo(
            run_id=run_id,
            failed_count=len(failed_rows),
            groups=groups,
            tasks=tasks,
        )

    def retry_failed_tasks(
        self,
        run_id: str,
        *,
        strategy: str = "immediate",
        max_retry_attempts: int = 3,
    ) -> RetryFailedTasksResult:
        run = self.db.query(DatahubJobRun).filter(DatahubJobRun.id == run_id).first()
        if run is None:
            raise BusinessException("作业记录不存在", code=ErrorCode.NOT_FOUND)
        if run.job_type != "backfill":
            raise BusinessException("仅支持 backfill 作业重试失败项", code=ErrorCode.VALIDATION_ERROR)
        if strategy not in {"immediate", "by_error"}:
            raise BusinessException("不支持的重试策略", code=ErrorCode.VALIDATION_ERROR)

        failed_tasks = (
            self.db.query(DatahubJobTask)
            .filter(
                DatahubJobTask.job_run_id == run_id,
                DatahubJobTask.status == DatahubTaskStatus.FAILED.value,
            )
            .order_by(DatahubJobTask.created_at.asc())
            .all()
        )
        if not failed_tasks:
            return RetryFailedTasksResult(created_runs=0, skipped_tasks=0, retried_tasks=0, retried_symbols=[])

        filtered_tasks: list[DatahubJobTask] = []
        skipped = 0
        for task in failed_tasks:
            if task.attempts >= max_retry_attempts:
                skipped += 1
                continue
            filtered_tasks.append(task)

        grouped: dict[tuple[str, date | None, date | None, str], list[DatahubJobTask]] = defaultdict(list)
        for task in filtered_tasks:
            error_key = task.last_error or "unknown"
            key = (
                task.dataset,
                task.start_date,
                task.end_date,
                error_key if strategy == "by_error" else "all",
            )
            grouped[key].append(task)

        created_runs = 0
        retried_symbols: list[str] = []
        for (_, start_date, end_date, _), tasks in grouped.items():
            if start_date is None or end_date is None:
                skipped += len(tasks)
                continue
            symbols = sorted({normalize_symbol(task.symbol) for task in tasks if task.symbol})
            if not symbols:
                skipped += len(tasks)
                continue
            payload = TriggerBackfillRequest(
                dataset="market_daily",
                start_date=start_date,
                end_date=end_date,
                symbols=symbols,
            )
            self.create_backfill_job(payload, trigger_source=f"retry:{run_id}")
            created_runs += 1
            retried_symbols.extend(symbols)

        return RetryFailedTasksResult(
            created_runs=created_runs,
            skipped_tasks=skipped,
            retried_tasks=len(filtered_tasks),
            retried_symbols=sorted(set(retried_symbols)),
        )

    def scan_market_daily_missing(
        self,
        *,
        start_date: date,
        end_date: date,
        reference_date: date | None = None,
        limit: int = 500,
    ) -> MarketDailyMissingScanResult:
        provider = BaoStockProvider()
        ref_date = reference_date or end_date
        rows = provider.get_security_master(day=ref_date)
        expected_symbols = sorted(
            {
                normalize_symbol(row_symbol)
                for row in rows
                for row_symbol in [row.get("symbol")]
                if row_symbol and row.get("status") == "active"
            }
        )
        existing_symbols = {
            normalize_symbol(item[0])
            for item in (
                self.db.query(DatahubObjectIndex.symbol)
                .filter(
                    DatahubObjectIndex.dataset == "market_daily",
                    DatahubObjectIndex.start_date == start_date,
                    DatahubObjectIndex.end_date == end_date,
                    DatahubObjectIndex.symbol.isnot(None),
                )
                .all()
            )
            if item[0]
        }
        missing_symbols = sorted([symbol for symbol in expected_symbols if symbol not in existing_symbols])
        return MarketDailyMissingScanResult(
            start_date=start_date,
            end_date=end_date,
            reference_date=ref_date,
            expected_count=len(expected_symbols),
            existing_count=len(existing_symbols),
            missing_count=len(missing_symbols),
            missing_symbols=missing_symbols[:limit],
        )

    def fill_market_daily_missing(
        self,
        *,
        start_date: date,
        end_date: date,
        reference_date: date | None = None,
        max_symbols: int = 500,
        batch_size: int = 200,
    ) -> FillMarketDailyMissingResult:
        scan = self.scan_market_daily_missing(
            start_date=start_date,
            end_date=end_date,
            reference_date=reference_date,
            limit=max_symbols,
        )
        symbols = scan.missing_symbols[:max_symbols]
        if not symbols:
            return FillMarketDailyMissingResult(created_runs=0, filled_symbols=0, symbols=[])

        created_runs = 0
        for i in range(0, len(symbols), batch_size):
            chunk = symbols[i : i + batch_size]
            payload = TriggerBackfillRequest(
                dataset="market_daily",
                start_date=start_date,
                end_date=end_date,
                symbols=chunk,
            )
            self.create_backfill_job(payload, trigger_source="auto-fill-missing")
            created_runs += 1
        return FillMarketDailyMissingResult(
            created_runs=created_runs,
            filled_symbols=len(symbols),
            symbols=symbols,
        )

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
