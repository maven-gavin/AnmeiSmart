import argparse
import logging
from typing import Sequence

from app.common.deps.database import SessionLocal
from app.core.api import BusinessException
from app.datahub.jobs.async_executor import execute_backfill_in_background
from app.datahub.schemas.datahub import TriggerBackfillRequest
from app.datahub.services import DatahubService

logger = logging.getLogger(__name__)


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="DataHub backfill job")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--start", required=True, dest="start_date")
    parser.add_argument("--end", required=True, dest="end_date")
    parser.add_argument("--symbol", required=False)
    args = parser.parse_args(argv)

    db = SessionLocal()
    try:
        service = DatahubService(db)
        request = TriggerBackfillRequest(
            dataset=args.dataset,
            start_date=args.start_date,
            end_date=args.end_date,
            symbol=args.symbol,
        )
        run = service.create_backfill_job(request, trigger_source="cli")
        logger.info("Created backfill run: %s", run.id)

        execute_backfill_in_background(run.id, request.model_dump(mode="python"))
        logger.info("%s backfill finished: %s", request.dataset, run.id)
    except BusinessException as exc:
        logger.error("backfill 业务错误: %s", exc.message, exc_info=True)
        raise
    except Exception as exc:
        logger.error("backfill 失败: %s", exc, exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
