from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.api import BusinessException, ErrorCode
from app.datahub.enums import DatahubTaskStatus
from app.datahub.models import DatahubDatasetWatermark, DatahubJobRun, DatahubJobTask
from app.datahub.schemas.datahub import TriggerDailyIncrementalRequest
from app.datahub.services.market_daily_backfill_service import MarketDailyBackfillService


class MarketDailyIncrementalService(MarketDailyBackfillService):
    def __init__(self, db: Session):
        super().__init__(db)

    def execute(self, run_id: str, payload: TriggerDailyIncrementalRequest) -> None:
        if payload.dataset != "market_daily":
            raise BusinessException("当前仅支持 market_daily 增量", code=ErrorCode.VALIDATION_ERROR)

        job_run = self._require_run(run_id)
        end_date = date.today()
        start_date = end_date - timedelta(days=payload.window_days)
        symbols = self._resolve_symbols(payload.symbol)

        self._prepare_run(job_run, len(symbols))
        tasks = self._create_tasks(run_id, symbols, start_date, end_date)

        success = 0
        failed = 0

        for task in tasks:
            self._mark_task_running(task)
            try:
                quality_score, object_key, is_fallback, watermark_date, can_publish = self.process_symbol(
                    symbol=task.symbol,
                    start_date=start_date,
                    end_date=end_date,
                    batch_prefix="daily",
                )
                if not is_fallback and can_publish:
                    self._upsert_watermark(
                        symbol=task.symbol,
                        end_date=watermark_date,
                        quality_score=quality_score,
                        object_key=object_key,
                        batch_prefix="daily",
                    )
                self._mark_task_success(task)
                success += 1
            except Exception as exc:
                self._mark_task_failed(task, str(exc))
                failed += 1

        self._finish_run(job_run, success=success, failed=failed)
        if failed > 0:
            raise BusinessException(
                f"daily incremental 部分失败：success={success}, failed={failed}",
                code=ErrorCode.BUSINESS_ERROR,
            )

    def _resolve_symbols(self, symbol: str | None) -> list[str]:
        if symbol:
            return [symbol]

        rows = (
            self.db.query(DatahubDatasetWatermark.symbol)
            .filter(
                DatahubDatasetWatermark.dataset == "market_daily",
                DatahubDatasetWatermark.symbol.isnot(None),
            )
            .all()
        )
        symbols = sorted({row.symbol for row in rows if row.symbol})
        if not symbols:
            raise BusinessException(
                "未找到可增量更新的 symbol，请先执行 backfill 或显式传入 --symbol",
                code=ErrorCode.BUSINESS_ERROR,
            )
        return symbols

    def _prepare_run(self, job_run: DatahubJobRun, total: int) -> None:
        job_run.status = DatahubTaskStatus.RUNNING.value
        job_run.started_at = datetime.now(timezone.utc)
        job_run.task_total = total
        job_run.task_success = 0
        job_run.task_failed = 0
        self.db.commit()

    def _create_tasks(self, run_id: str, symbols: list[str], start_date: date, end_date: date) -> list[DatahubJobTask]:
        tasks: list[DatahubJobTask] = []
        for symbol in symbols:
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
        if failed > 0:
            job_run.error_message = f"partial_failed: success={success}, failed={failed}"
        else:
            job_run.error_message = None
        self.db.commit()
