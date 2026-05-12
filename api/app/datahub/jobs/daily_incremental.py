import argparse
import logging
from typing import Sequence

from app.common.deps.database import SessionLocal
from app.core.api import BusinessException
from app.datahub.jobs.async_executor import execute_daily_incremental_in_background
from app.datahub.schemas.datahub import TriggerDailyIncrementalRequest
from app.datahub.services import DatahubService

logger = logging.getLogger(__name__)


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="DataHub daily incremental job")
    parser.add_argument("--dataset", required=False, default="market_daily")
    parser.add_argument("--symbol", required=False)
    parser.add_argument("--window-days", required=False, type=int, default=7, dest="window_days")
    args = parser.parse_args(argv)

    db = SessionLocal()
    try:
        service = DatahubService(db)
        request = TriggerDailyIncrementalRequest(
            dataset=args.dataset,
            symbol=args.symbol,
            window_days=args.window_days,
        )
        run = service.create_daily_incremental_job(
            request,
            trigger_source="cli",
        )
        logger.info("Created daily incremental run: %s", run.id)
        execute_daily_incremental_in_background(run.id, request.model_dump(mode="python"))
        logger.info("%s daily incremental finished: %s", request.dataset, run.id)
    except BusinessException as exc:
        logger.error("daily incremental 业务错误: %s", exc.message, exc_info=True)
        raise
    except Exception as exc:
        logger.error("daily incremental 失败: %s", exc, exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
