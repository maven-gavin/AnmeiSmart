from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta, timezone
from io import BytesIO

from sqlalchemy.orm import Session

from app.core.api import BusinessException, ErrorCode
from app.core.config import get_settings
from app.datahub.enums import DatahubTaskStatus
from app.datahub.models import DatahubDatasetWatermark, DatahubJobRun, DatahubJobTask
from app.datahub.normalize import normalize_symbol
from app.datahub.providers import BaoStockProvider
from app.datahub.schemas.datahub import TriggerBackfillRequest
from app.datahub.services.quality_service import DatahubQualityService
from app.datahub.services.storage_service import DatahubStorageService
from app.datahub.storage import MinioParquetStore


class MarketDailyBackfillService:
    def __init__(self, db: Session):
        self.db = db
        self.provider = BaoStockProvider()
        self.storage_service = DatahubStorageService(db)
        self.quality_service = DatahubQualityService(db)

    def execute(self, run_id: str, payload: TriggerBackfillRequest) -> None:
        job_run = self._require_run(run_id)
        placeholder_task = self._require_task(run_id)
        symbols = self._resolve_symbols(payload.symbol, payload.end_date)
        tasks = self._prepare_tasks(
            run_id=run_id,
            placeholder_task=placeholder_task,
            symbols=symbols,
            start_date=payload.start_date,
            end_date=payload.end_date,
        )

        self._prepare_run(job_run, total=len(tasks))

        success = 0
        failed = 0
        for task in tasks:
            self._mark_task_running(task)
            try:
                task_symbol = task.symbol or ""
                quality_score, object_key = self.process_symbol(
                    symbol=task_symbol,
                    start_date=payload.start_date,
                    end_date=payload.end_date,
                    batch_prefix="backfill",
                )
                self._upsert_watermark(
                    symbol=task_symbol,
                    end_date=payload.end_date,
                    quality_score=quality_score,
                    object_key=object_key,
                    batch_prefix="backfill",
                )
                self._mark_task_success(task)
                success += 1
            except Exception as exc:
                self._mark_task_failed(task, str(exc))
                failed += 1

        self._finish_run(job_run, success=success, failed=failed)
        if failed > 0:
            raise BusinessException(
                f"market_daily backfill 部分失败：success={success}, failed={failed}",
                code=ErrorCode.BUSINESS_ERROR,
            )

    def process_symbol(
        self,
        *,
        symbol: str,
        start_date: date,
        end_date: date,
        batch_prefix: str,
    ) -> tuple[float, str]:
        rows = self.provider.get_daily_bars(symbol, start_date, end_date)
        if not rows:
            raise BusinessException("未获取到任何 market_daily 数据", code=ErrorCode.BUSINESS_ERROR)

        parquet_bytes = self._to_parquet_bytes(rows)
        object_key = self._build_object_key(symbol=symbol, end_date=end_date, batch_prefix=batch_prefix)
        store = MinioParquetStore()
        store.put_bytes(object_key=object_key, data=parquet_bytes, content_type="application/octet-stream")

        quality_score, issues, severity = self._quality_check(rows)
        bucket = get_settings().MINIO_BUCKET_NAME
        self.storage_service.upsert_object_index(
            bucket=bucket,
            object_key=object_key,
            dataset="market_daily",
            layer="normalized",
            provider="baostock",
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            row_count=len(rows),
            schema_version="1.0",
            content_hash=hashlib.sha256(parquet_bytes).hexdigest(),
        )

        self.quality_service.write_report(
            dataset="market_daily",
            symbol=symbol,
            quality_score=quality_score,
            severity=severity,
            issues=issues,
            object_key=object_key,
        )
        return quality_score, object_key

    def _upsert_watermark(
        self,
        *,
        symbol: str,
        end_date: date,
        quality_score: float,
        object_key: str,
        batch_prefix: str,
    ) -> None:
        row = (
            self.db.query(DatahubDatasetWatermark)
            .filter(
                DatahubDatasetWatermark.dataset == "market_daily",
                DatahubDatasetWatermark.symbol == symbol,
            )
            .first()
        )
        if row is None:
            row = DatahubDatasetWatermark(dataset="market_daily", symbol=symbol)
            self.db.add(row)
        row.last_success_date = end_date
        row.last_quality_score = quality_score
        row.last_object_key = object_key
        row.last_batch_id = f"{batch_prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        self.db.commit()

    @staticmethod
    def _to_parquet_bytes(rows: list[dict]) -> bytes:
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
        except Exception as exc:  # pragma: no cover
            raise BusinessException(
                "缺少 pyarrow 依赖，无法写入 Parquet",
                code=ErrorCode.SYSTEM_ERROR,
                details={"error": str(exc)},
            ) from exc

        table = pa.Table.from_pylist(rows)
        sink = BytesIO()
        pq.write_table(table, sink, compression="snappy")
        return sink.getvalue()

    @staticmethod
    def _quality_check(rows: list[dict]) -> tuple[float, list[dict], str]:
        issues: list[dict] = []
        invalid_price_count = 0
        for row in rows:
            if row["open"] <= 0 or row["high"] <= 0 or row["low"] <= 0 or row["close"] <= 0:
                invalid_price_count += 1

        if invalid_price_count > 0:
            issues.append(
                {
                    "rule": "price_positive_check",
                    "message": "存在价格小于等于0的记录",
                    "count": invalid_price_count,
                }
            )

        total = len(rows)
        score = max(0.0, 100.0 - (invalid_price_count / total) * 100.0)
        if invalid_price_count == 0:
            return score, issues, "p2"
        if invalid_price_count <= max(1, int(total * 0.05)):
            return score, issues, "p1"
        return score, issues, "p0"

    @staticmethod
    def _build_object_key(*, symbol: str, end_date: date, batch_prefix: str) -> str:
        batch_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return (
            "datahub/normalized/"
            f"dataset=market_daily/year={end_date.year}/month={end_date.month:02d}/"
            f"symbol={symbol}/batch_id={batch_prefix}-{batch_id}.parquet"
        )

    def _resolve_symbols(self, symbol: str | None, end_date: date) -> list[str]:
        if symbol:
            return [normalize_symbol(symbol)]

        rows = self._load_security_master_rows(end_date=end_date)
        symbols = sorted(
            {
                normalize_symbol(row_symbol)
                for row in rows
                for row_symbol in [row.get("symbol")]
                if row_symbol
            }
        )
        if not symbols:
            raise BusinessException(
                "未提供 symbol，且无法获取可回填证券列表，请检查 security_master 数据源",
                code=ErrorCode.BUSINESS_ERROR,
            )
        return symbols

    def _load_security_master_rows(self, *, end_date: date) -> list[dict]:
        for offset in range(0, 8):
            day = end_date - timedelta(days=offset)
            rows = self.provider.get_security_master(day=day)
            if rows:
                return rows
        return []

    def _prepare_tasks(
        self,
        *,
        run_id: str,
        placeholder_task: DatahubJobTask,
        symbols: list[str],
        start_date: date,
        end_date: date,
    ) -> list[DatahubJobTask]:
        placeholder_task.dataset = "market_daily"
        placeholder_task.symbol = symbols[0]
        placeholder_task.start_date = start_date
        placeholder_task.end_date = end_date
        placeholder_task.status = DatahubTaskStatus.PENDING.value
        placeholder_task.last_error = None
        placeholder_task.locked_at = None
        placeholder_task.attempts = 0
        tasks = [placeholder_task]

        for symbol in symbols[1:]:
            task = DatahubJobTask(
                job_run_id=run_id,
                dataset="market_daily",
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

    def _require_run(self, run_id: str) -> DatahubJobRun:
        row = self.db.query(DatahubJobRun).filter(DatahubJobRun.id == run_id).first()
        if row is None:
            raise BusinessException("作业不存在", code=ErrorCode.NOT_FOUND)
        return row

    def _require_task(self, run_id: str) -> DatahubJobTask:
        row = self.db.query(DatahubJobTask).filter(DatahubJobTask.job_run_id == run_id).first()
        if row is None:
            raise BusinessException("作业任务不存在", code=ErrorCode.NOT_FOUND)
        return row

    def _prepare_run(self, job_run: DatahubJobRun, total: int) -> None:
        job_run.status = DatahubTaskStatus.RUNNING.value
        job_run.started_at = datetime.now(timezone.utc)
        job_run.task_total = total
        job_run.task_success = 0
        job_run.task_failed = 0
        job_run.error_message = None
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

    def _finish_run(self, job_run: DatahubJobRun, *, success: int, failed: int) -> None:
        job_run.task_success = success
        job_run.task_failed = failed
        job_run.status = DatahubTaskStatus.SUCCESS.value if failed == 0 else DatahubTaskStatus.FAILED.value
        job_run.finished_at = datetime.now(timezone.utc)
        job_run.error_message = None if failed == 0 else f"partial_failed: success={success}, failed={failed}"
        self.db.commit()
