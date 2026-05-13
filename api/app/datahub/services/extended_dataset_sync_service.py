from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.api import BusinessException, ErrorCode
from app.core.config import get_settings
from app.datahub.enums import DatahubTaskStatus
from app.datahub.models import DatahubDatasetWatermark, DatahubJobRun, DatahubJobTask, DatahubObjectIndex
from app.datahub.normalize import normalize_symbol
from app.datahub.providers import BaoStockProvider, EastMoneyProvider
from app.datahub.schemas.datahub import TriggerBackfillRequest, TriggerDailyIncrementalRequest
from app.datahub.services.market_daily_backfill_service import MarketDailyBackfillService
from app.datahub.services.provider_health_service import DatahubProviderHealthService
from app.datahub.services.quality_service import DatahubQualityService
from app.datahub.services.router_service import DatahubRouterService
from app.datahub.services.storage_service import DatahubStorageService
from app.datahub.storage import MinioParquetStore


class ExtendedDatasetSyncService:
    SUPPORTED_DATASETS = {"money_flow", "sector_members", "financial_summary"}
    SNAPSHOT_DATASETS = {"sector_members"}

    def __init__(self, db: Session):
        self.db = db
        self.providers = {
            "baostock": BaoStockProvider(),
            "eastmoney": EastMoneyProvider(),
        }
        self.router_service = DatahubRouterService()
        self.storage_service = DatahubStorageService(db)
        self.quality_service = DatahubQualityService(db)
        self.provider_health_service = DatahubProviderHealthService(db)

    def execute_backfill(self, run_id: str, payload: TriggerBackfillRequest) -> None:
        if payload.dataset not in self.SUPPORTED_DATASETS:
            raise BusinessException(f"不支持的数据集: {payload.dataset}", code=ErrorCode.VALIDATION_ERROR)
        run = self._require_run(run_id)
        symbols = self._resolve_symbols(dataset=payload.dataset, symbol=payload.symbol, symbols=payload.symbols, end_date=payload.end_date)
        tasks = self._prepare_tasks(run_id=run_id, dataset=payload.dataset, start_date=payload.start_date, end_date=payload.end_date, symbols=symbols)
        self._prepare_run(run, total=len(tasks))
        self._run_tasks(run=run, tasks=tasks, dataset=payload.dataset, start_date=payload.start_date, end_date=payload.end_date, batch_prefix="backfill")

    def execute_daily_incremental(self, run_id: str, payload: TriggerDailyIncrementalRequest) -> None:
        if payload.dataset not in self.SUPPORTED_DATASETS:
            raise BusinessException(f"不支持的数据集: {payload.dataset}", code=ErrorCode.VALIDATION_ERROR)
        run = self._require_run(run_id)
        end_date = date.today()
        start_date = end_date - timedelta(days=payload.window_days)
        symbols = self._resolve_symbols(dataset=payload.dataset, symbol=payload.symbol, symbols=None, end_date=end_date)
        tasks = self._prepare_tasks(run_id=run_id, dataset=payload.dataset, start_date=start_date, end_date=end_date, symbols=symbols)
        self._prepare_run(run, total=len(tasks))
        self._run_tasks(run=run, tasks=tasks, dataset=payload.dataset, start_date=start_date, end_date=end_date, batch_prefix="daily")

    def _run_tasks(
        self,
        *,
        run: DatahubJobRun,
        tasks: list[DatahubJobTask],
        dataset: str,
        start_date: date,
        end_date: date,
        batch_prefix: str,
    ) -> None:
        success = 0
        failed = 0
        for task in tasks:
            self._mark_task_running(task)
            symbol = task.symbol
            try:
                quality_score, object_key, is_fallback, watermark_date, can_publish = self._process_task(
                    dataset=dataset,
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    batch_prefix=batch_prefix,
                )
                if not is_fallback and can_publish:
                    self._upsert_watermark(
                        dataset=dataset,
                        symbol=symbol,
                        end_date=watermark_date,
                        quality_score=quality_score,
                        object_key=object_key,
                        batch_prefix=batch_prefix,
                    )
                self._mark_task_success(task)
                success += 1
            except Exception as exc:
                self._mark_task_failed(task, str(exc))
                failed += 1
        self._finish_run(run, success=success, failed=failed)
        if failed > 0:
            raise BusinessException(
                f"{dataset} 同步部分失败：success={success}, failed={failed}",
                code=ErrorCode.BUSINESS_ERROR,
            )

    def _process_task(
        self,
        *,
        dataset: str,
        symbol: str | None,
        start_date: date,
        end_date: date,
        batch_prefix: str,
    ) -> tuple[float, str, bool, date, bool]:
        rows, provider_name = self._load_rows(dataset=dataset, symbol=symbol, start_date=start_date, end_date=end_date)
        if not rows:
            snapshot = self._get_stable_snapshot(dataset=dataset, symbol=symbol, required_end_date=end_date)
            if snapshot is not None:
                score, object_key, snapshot_date = snapshot
                self.quality_service.write_report(
                    dataset=dataset,
                    symbol=symbol,
                    quality_score=score,
                    severity="p1",
                    issues=[
                        {
                            "rule": "provider_fallback_snapshot",
                            "message": f"{dataset} 源站失败，降级使用 MinIO 稳定快照",
                            "snapshot_date": snapshot_date.isoformat(),
                        }
                    ],
                    object_key=object_key,
                )
                return score, object_key, True, snapshot_date, False
            raise BusinessException(f"{dataset} 未获取到有效数据", code=ErrorCode.BUSINESS_ERROR)

        parquet_bytes = MarketDailyBackfillService._to_parquet_bytes(rows)
        object_key = self._build_object_key(dataset=dataset, symbol=symbol, end_date=end_date, batch_prefix=batch_prefix)
        MinioParquetStore().put_bytes(object_key=object_key, data=parquet_bytes, content_type="application/octet-stream")

        quality_score, issues, severity = self._quality_check(rows)
        self.storage_service.upsert_object_index(
            bucket=get_settings().MINIO_BUCKET_NAME,
            object_key=object_key,
            dataset=dataset,
            layer="normalized",
            provider=provider_name,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            row_count=len(rows),
            schema_version="1.0",
            content_hash=hashlib.sha256(parquet_bytes).hexdigest(),
            quality_score=quality_score,
        )
        self.quality_service.write_report(
            dataset=dataset,
            symbol=symbol,
            quality_score=quality_score,
            severity=severity,
            issues=issues,
            object_key=object_key,
        )
        can_publish = self.quality_service.can_publish_latest(dataset, quality_score)
        if can_publish:
            self.storage_service.publish_latest_manifest(
                dataset=dataset,
                symbol=symbol,
                object_key=object_key,
                schema_version="1.0",
                quality_score=quality_score,
                start_date=start_date,
                end_date=end_date,
            )
        return quality_score, object_key, False, end_date, can_publish

    def _load_rows(
        self,
        *,
        dataset: str,
        symbol: str | None,
        start_date: date,
        end_date: date,
    ) -> tuple[list[dict], str]:
        priorities = self.router_service.get_provider_priority(dataset)
        errors: list[str] = []
        for provider_name in priorities:
            if provider_name == "minio_cache":
                continue
            provider = self.providers.get(provider_name)
            if provider is None:
                errors.append(f"{provider_name} 未接入")
                continue
            if not self.provider_health_service.is_available(provider=provider_name, dataset=dataset):
                errors.append(f"{provider_name} 处于熔断冷却")
                continue
            try:
                if dataset == "money_flow":
                    if symbol is None:
                        raise BusinessException("money_flow 需要 symbol", code=ErrorCode.VALIDATION_ERROR)
                    rows = self.router_service.run_with_policy(
                        dataset=dataset,
                        provider=provider_name,
                        operation=lambda: provider.get_money_flow(symbol=symbol, start_date=start_date, end_date=end_date),
                    )
                elif dataset == "sector_members":
                    rows = self._load_sector_members(provider_name=provider_name, provider=provider, asof_date=end_date)
                elif dataset == "financial_summary":
                    if symbol is None:
                        raise BusinessException("financial_summary 需要 symbol", code=ErrorCode.VALIDATION_ERROR)
                    rows = self.router_service.run_with_policy(
                        dataset=dataset,
                        provider=provider_name,
                        operation=lambda: provider.get_financial_statement(symbol=symbol, start_date=start_date, end_date=end_date),
                    )
                else:
                    rows = []
            except Exception as exc:
                self.provider_health_service.record_failure(provider=provider_name, dataset=dataset, error=str(exc))
                errors.append(f"{provider_name} 失败: {exc}")
                continue
            if not rows:
                self.provider_health_service.record_failure(provider=provider_name, dataset=dataset, error="查询结果为空")
                errors.append(f"{provider_name} 返回空数据")
                continue
            self.provider_health_service.record_success(provider=provider_name, dataset=dataset)
            return rows, provider_name
        raise BusinessException(f"{dataset} provider 获取失败: {' | '.join(errors)}", code=ErrorCode.BUSINESS_ERROR)

    def _load_sector_members(self, *, provider_name: str, provider, asof_date: date) -> list[dict]:
        sectors = self.router_service.run_with_policy(
            dataset="sector_members",
            provider=provider_name,
            operation=provider.get_sector_list,
        )
        rows: list[dict] = []
        for sector in sectors[:200]:
            sector_code = str(sector.get("sector_code") or sector.get("sector_name") or "").strip()
            if not sector_code:
                continue
            items = self.router_service.run_with_policy(
                dataset="sector_members",
                provider=provider_name,
                operation=lambda: provider.get_sector_members(sector_code=sector_code, asof_date=asof_date),
            )
            rows.extend(items)
        return rows

    def _resolve_symbols(
        self,
        *,
        dataset: str,
        symbol: str | None,
        symbols: list[str] | None,
        end_date: date,
    ) -> list[str | None]:
        if dataset in self.SNAPSHOT_DATASETS:
            return [None]
        if symbols:
            normalized = sorted({normalize_symbol(item) for item in symbols if item})
            if normalized:
                return normalized
        if symbol:
            return [normalize_symbol(symbol)]

        baostock = self.providers["baostock"]
        rows = baostock.get_security_master(day=end_date)
        resolved = sorted(
            {
                normalize_symbol(code)
                for item in rows
                for code in [item.get("symbol")]
                if code and item.get("status") == "active"
            }
        )
        if not resolved:
            raise BusinessException(f"{dataset} 无可用 symbol，请先同步 security_master", code=ErrorCode.BUSINESS_ERROR)
        return resolved

    def _prepare_tasks(
        self,
        *,
        run_id: str,
        dataset: str,
        start_date: date,
        end_date: date,
        symbols: list[str | None],
    ) -> list[DatahubJobTask]:
        old_tasks = self.db.query(DatahubJobTask).filter(DatahubJobTask.job_run_id == run_id).all()
        for old in old_tasks:
            self.db.delete(old)
        self.db.flush()

        tasks: list[DatahubJobTask] = []
        for symbol in symbols:
            task = DatahubJobTask(
                job_run_id=run_id,
                dataset=dataset,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                status=DatahubTaskStatus.PENDING.value,
                attempts=0,
            )
            self.db.add(task)
            tasks.append(task)
        self.db.commit()
        for task in tasks:
            self.db.refresh(task)
        return tasks

    def _get_stable_snapshot(
        self,
        *,
        dataset: str,
        symbol: str | None,
        required_end_date: date,
    ) -> tuple[float, str, date] | None:
        query = self.db.query(DatahubDatasetWatermark).filter(DatahubDatasetWatermark.dataset == dataset)
        if symbol is None:
            query = query.filter(DatahubDatasetWatermark.symbol == "__ALL__")
        else:
            query = query.filter(DatahubDatasetWatermark.symbol == symbol)
        watermark = query.first()
        if (
            watermark is None
            or not watermark.last_object_key
            or watermark.last_quality_score is None
            or watermark.last_success_date is None
        ):
            return None
        if watermark.last_quality_score < 90:
            return None
        if watermark.last_success_date < required_end_date:
            return None
        if not MinioParquetStore().exists(watermark.last_object_key):
            return None
        indexed = self.db.query(DatahubObjectIndex.id).filter(DatahubObjectIndex.object_key == watermark.last_object_key).first()
        if indexed is None:
            return None
        return float(watermark.last_quality_score), watermark.last_object_key, watermark.last_success_date

    def _upsert_watermark(
        self,
        *,
        dataset: str,
        symbol: str | None,
        end_date: date,
        quality_score: float,
        object_key: str,
        batch_prefix: str,
    ) -> None:
        watermark_symbol = "__ALL__" if symbol is None else symbol
        row = (
            self.db.query(DatahubDatasetWatermark)
            .filter(
                DatahubDatasetWatermark.dataset == dataset,
                DatahubDatasetWatermark.symbol == watermark_symbol,
            )
            .first()
        )
        if row is None:
            row = DatahubDatasetWatermark(dataset=dataset, symbol=watermark_symbol)
            self.db.add(row)
        row.last_success_date = end_date
        row.last_quality_score = quality_score
        row.last_object_key = object_key
        row.last_batch_id = f"{batch_prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        self.db.commit()

    @staticmethod
    def _quality_check(rows: list[dict]) -> tuple[float, list[dict], str]:
        total = len(rows)
        missing = 0
        for item in rows:
            for value in item.values():
                if value in (None, "", "NaN"):
                    missing += 1
        score = max(0.0, 100.0 - (missing / max(total, 1)))
        issues = [{"rule": "missing_values", "count": missing}] if missing > 0 else []
        if missing == 0:
            severity = "p2"
        elif missing <= max(5, total // 10):
            severity = "p1"
        else:
            severity = "p0"
        return score, issues, severity

    @staticmethod
    def _build_object_key(*, dataset: str, symbol: str | None, end_date: date, batch_prefix: str) -> str:
        batch_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        symbol_part = f"/symbol={symbol}" if symbol else ""
        return (
            "datahub/normalized/"
            f"dataset={dataset}/year={end_date.year}/month={end_date.month:02d}"
            f"{symbol_part}/batch_id={batch_prefix}-{batch_id}.parquet"
        )

    def _prepare_run(self, run: DatahubJobRun, *, total: int) -> None:
        run.status = DatahubTaskStatus.RUNNING.value
        run.started_at = datetime.now(timezone.utc)
        run.task_total = total
        run.task_success = 0
        run.task_failed = 0
        run.error_message = None
        self.db.commit()

    def _finish_run(self, run: DatahubJobRun, *, success: int, failed: int) -> None:
        run.task_success = success
        run.task_failed = failed
        run.status = DatahubTaskStatus.SUCCESS.value if failed == 0 else DatahubTaskStatus.FAILED.value
        run.finished_at = datetime.now(timezone.utc)
        run.error_message = None if failed == 0 else f"partial_failed: success={success}, failed={failed}"
        self.db.commit()

    def _mark_task_running(self, task: DatahubJobTask) -> None:
        task.status = DatahubTaskStatus.RUNNING.value
        task.locked_at = datetime.now(timezone.utc)
        task.attempts = task.attempts + 1
        self.db.commit()

    def _mark_task_success(self, task: DatahubJobTask) -> None:
        task.status = DatahubTaskStatus.SUCCESS.value
        task.last_error = None
        self.db.commit()

    def _mark_task_failed(self, task: DatahubJobTask, message: str) -> None:
        task.status = DatahubTaskStatus.FAILED.value
        task.last_error = message[:2000]
        self.db.commit()

    def _require_run(self, run_id: str) -> DatahubJobRun:
        row = self.db.query(DatahubJobRun).filter(DatahubJobRun.id == run_id).first()
        if row is None:
            raise BusinessException("作业不存在", code=ErrorCode.NOT_FOUND)
        return row
