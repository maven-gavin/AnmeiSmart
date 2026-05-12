import argparse
import logging
import time

from app.common.deps.database import SessionLocal
from app.datahub.jobs.async_executor import execute_run_by_id
from app.datahub.services import DatahubService

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="DataHub worker loop")
    parser.add_argument("--poll-seconds", type=int, default=5, dest="poll_seconds")
    parser.add_argument("--batch-size", type=int, default=5, dest="batch_size")
    parser.add_argument("--worker-name", type=str, default="datahub-default-worker", dest="worker_name")
    args = parser.parse_args()

    logger.info(
        "DataHub worker started, worker_name=%s poll_seconds=%s batch_size=%s",
        args.worker_name,
        args.poll_seconds,
        args.batch_size,
    )
    while True:
        db = SessionLocal()
        try:
            service = DatahubService(db)
            service.upsert_worker_heartbeat(worker_name=args.worker_name, status="idle")
            run_ids = service.list_pending_run_ids(limit=args.batch_size)
        finally:
            db.close()

        if not run_ids:
            time.sleep(args.poll_seconds)
            continue

        for run_id in run_ids:
            db = SessionLocal()
            try:
                DatahubService(db).upsert_worker_heartbeat(
                    worker_name=args.worker_name,
                    status="running",
                    last_run_id=run_id,
                )
            finally:
                db.close()
            try:
                execute_run_by_id(run_id)
                db = SessionLocal()
                try:
                    DatahubService(db).upsert_worker_heartbeat(
                        worker_name=args.worker_name,
                        status="idle",
                        last_run_id=run_id,
                        increment_processed=True,
                    )
                finally:
                    db.close()
            except Exception as exc:
                db = SessionLocal()
                try:
                    DatahubService(db).upsert_worker_heartbeat(
                        worker_name=args.worker_name,
                        status="error",
                        last_run_id=run_id,
                        last_error=str(exc),
                    )
                finally:
                    db.close()
                logger.error("Worker process run failed run_id=%s error=%s", run_id, exc, exc_info=True)


if __name__ == "__main__":
    main()
