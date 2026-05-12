import argparse

from app.datahub.jobs.backfill import main as backfill_main
from app.datahub.jobs.daily_incremental import main as daily_incremental_main
from app.datahub.jobs.worker import main as worker_main


def main() -> None:
    parser = argparse.ArgumentParser(description="DataHub CLI")
    parser.add_argument("command", choices=["backfill", "daily_incremental", "worker"])
    args, rest = parser.parse_known_args()

    if args.command == "backfill":
        backfill_main(rest)
        return
    if args.command == "daily_incremental":
        daily_incremental_main(rest)
        return
    worker_main()


if __name__ == "__main__":
    main()
