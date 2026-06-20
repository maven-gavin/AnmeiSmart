from datetime import date, datetime, timezone

from app.datahub.schemas.datahub import (
    DatahubJobRunInfo,
    DatahubWorkerHeartbeatInfo,
    WatchlistBoardResponse,
    WatchlistBoardRow,
)
from app.datahub.services.daily_brief_service import DailyBriefService
from app.datahub.services.context_export_service import ContextExportService


class FakeDatahubService:
    def __init__(self, heartbeat: DatahubWorkerHeartbeatInfo | None = None) -> None:
        self.heartbeat = heartbeat
        self.created_payloads: list[object] = []

    def get_worker_heartbeat(
        self,
        worker_name: str = "datahub-default-worker",
        offline_threshold_seconds: int = 30,
    ) -> DatahubWorkerHeartbeatInfo | None:
        return self.heartbeat

    def create_daily_incremental_job(self, payload: object, trigger_source: str = "api") -> DatahubJobRunInfo:
        self.created_payloads.append(payload)
        return DatahubJobRunInfo(
            id="run_1",
            job_type="daily_incremental",
            dataset="market_daily",
            status="pending",
            trigger_source=trigger_source,
            started_at=None,
            finished_at=None,
            task_total=0,
            task_success=0,
            task_failed=0,
            error_message=None,
            created_at=datetime(2026, 6, 20, tzinfo=timezone.utc),
            updated_at=datetime(2026, 6, 20, tzinfo=timezone.utc),
        )


class FakeWatchlistService:
    def __init__(self, board: WatchlistBoardResponse) -> None:
        self.board = board

    def get_board(self, *, limit_days: int = 30) -> WatchlistBoardResponse:
        return self.board


class FakeMarketDailyReadService:
    def get_bars(self, *, symbol: str, start_date: date, end_date: date) -> list[dict]:
        return [
            {
                "symbol": symbol,
                "trade_date": date(2026, 6, 19),
                "open": 10,
                "high": 11,
                "low": 9,
                "close": 10.5,
                "volume": 1000,
                "amount": 10500,
                "turnover_rate": 2.1,
            }
        ]


def test_daily_brief_readiness_marks_worker_offline_and_missing_watchlist_data() -> None:
    board = WatchlistBoardResponse(
        limit_days=10,
        rows=[
            WatchlistBoardRow(
                id="w1",
                symbol="600000",
                name="浦发银行",
                trade_date=None,
                close=None,
                has_data=False,
            )
        ],
    )
    service = DailyBriefService(
        datahub_service=FakeDatahubService(heartbeat=None),
        watchlist_service=FakeWatchlistService(board),
    )

    readiness = service.get_readiness()

    assert readiness.status == "worker_offline"
    assert readiness.watchlist_count == 1
    assert readiness.missing_count == 1
    assert any("Worker 未在线" in warning for warning in readiness.warnings)


def test_context_export_returns_opencode_payload_with_daily_brief_context() -> None:
    heartbeat = DatahubWorkerHeartbeatInfo(
        worker_name="datahub-default-worker",
        status="idle",
        last_heartbeat_at=datetime(2026, 6, 20, tzinfo=timezone.utc),
        last_run_id=None,
        processed_count=3,
        last_error=None,
        is_online=True,
        offline_threshold_seconds=30,
    )
    board = WatchlistBoardResponse(
        limit_days=10,
        rows=[
            WatchlistBoardRow(
                id="w1",
                symbol="600000",
                name="浦发银行",
                sector_name="银行",
                trade_date=date(2026, 6, 19),
                close=10.5,
                change_pct=1.2,
                sector_change_pct=0.8,
                volume=1000,
                turnover_rate=2.1,
                has_data=True,
            )
        ],
    )
    daily_service = DailyBriefService(
        datahub_service=FakeDatahubService(heartbeat=heartbeat),
        watchlist_service=FakeWatchlistService(board),
    )
    export_service = ContextExportService(
        daily_brief_service=daily_service,
        market_daily_read_service=FakeMarketDailyReadService(),
    )

    payload = export_service.get_opencode_context(as_of_date=date(2026, 6, 20))

    assert payload["kind"] == "datahub.opencode.daily_context"
    assert payload["context"]["readiness"]["status"] == "ready"
    assert payload["context"]["watchlist"][0]["symbol"] == "600000"
    assert payload["usage_hint"].startswith("将该 JSON")
