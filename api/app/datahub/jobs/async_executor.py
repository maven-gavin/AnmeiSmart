import logging

from app.common.deps.database import SessionLocal
from app.datahub.schemas.datahub import TriggerBackfillRequest, TriggerDailyIncrementalRequest
from app.datahub.models import DatahubJobRun
from app.datahub.services import (
    DatahubService,
    ExtendedDatasetSyncService,
    MarketDailyBackfillService,
    MarketDailyIncrementalService,
    SecurityMasterSyncService,
    TradingCalendarSyncService,
)

logger = logging.getLogger(__name__)


def _execute_backfill_with_db(run_id: str, payload_data: dict, service: DatahubService) -> None:
    db = service.db
    try:
        payload = TriggerBackfillRequest.model_validate(payload_data)
        if payload.dataset == "market_daily":
            MarketDailyBackfillService(db).execute(run_id, payload)
            return
        if payload.dataset == "security_master":
            SecurityMasterSyncService(db).execute_backfill(run_id, payload)
            return
        if payload.dataset == "trading_calendar":
            TradingCalendarSyncService(db).execute_backfill(run_id, payload)
            return
        if payload.dataset in {"money_flow", "sector_members", "financial_summary"}:
            ExtendedDatasetSyncService(db).execute_backfill(run_id, payload)
            return

        service.mark_run_failed(run_id, f"unsupported backfill dataset: {payload.dataset}")
    except Exception as exc:
        logger.error("Backfill background execution failed: %s", exc, exc_info=True)
        service.mark_run_failed(run_id, str(exc))


def _execute_daily_with_db(run_id: str, payload_data: dict, service: DatahubService) -> None:
    db = service.db
    try:
        payload = TriggerDailyIncrementalRequest.model_validate(payload_data)
        if payload.dataset == "market_daily":
            MarketDailyIncrementalService(db).execute(run_id, payload)
            return
        if payload.dataset == "security_master":
            SecurityMasterSyncService(db).execute_daily_incremental(run_id, payload)
            return
        if payload.dataset == "trading_calendar":
            TradingCalendarSyncService(db).execute_daily_incremental(run_id, payload)
            return
        if payload.dataset in {"money_flow", "sector_members", "financial_summary"}:
            ExtendedDatasetSyncService(db).execute_daily_incremental(run_id, payload)
            return

        service.mark_run_failed(run_id, f"unsupported daily dataset: {payload.dataset}")
    except Exception as exc:
        logger.error("Daily incremental background execution failed: %s", exc, exc_info=True)
        service.mark_run_failed(run_id, str(exc))


def execute_run_by_id(run_id: str) -> None:
    db = SessionLocal()
    try:
        service = DatahubService(db)
        run = db.query(DatahubJobRun).filter(DatahubJobRun.id == run_id).first()
        if run is None:
            logger.warning("Run not found: %s", run_id)
            return
        payload_data = run.job_params or {}
        if run.job_type == "backfill":
            _execute_backfill_with_db(run_id, payload_data, service)
            return
        if run.job_type == "daily_incremental":
            _execute_daily_with_db(run_id, payload_data, service)
            return
        service.mark_run_failed(run_id, f"unsupported job_type: {run.job_type}")
    except Exception as exc:
        logger.error("Run execution failed run_id=%s: %s", run_id, exc, exc_info=True)
        DatahubService(db).mark_run_failed(run_id, str(exc))
    finally:
        db.close()


def execute_backfill_in_background(run_id: str, payload_data: dict) -> None:
    db = SessionLocal()
    try:
        _execute_backfill_with_db(run_id, payload_data, DatahubService(db))
    finally:
        db.close()


def execute_daily_incremental_in_background(run_id: str, payload_data: dict) -> None:
    db = SessionLocal()
    try:
        _execute_daily_with_db(run_id, payload_data, DatahubService(db))
    finally:
        db.close()
