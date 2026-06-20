from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.datahub.schemas.daily_brief import (
    DailyBriefContextInfo,
    DailyBriefMarketInfo,
    DailyBriefPrepareResultInfo,
    DailyBriefReadinessInfo,
    DailyBriefRiskFlagInfo,
    DailyBriefSectorInfo,
    DailyBriefWatchlistItemInfo,
)
from app.datahub.schemas.datahub import TriggerDailyIncrementalRequest, WatchlistBoardResponse, WatchlistBoardRow
from app.datahub.services.datahub_service import DatahubService
from app.datahub.services.watchlist_service import DatahubWatchlistService


class DailyBriefService:
    """生成每日看盘和 AI 分析使用的结构化上下文。"""

    def __init__(
        self,
        db: Session | None = None,
        datahub_service: DatahubService | None = None,
        watchlist_service: DatahubWatchlistService | None = None,
    ):
        if db is None and (datahub_service is None or watchlist_service is None):
            raise ValueError("db 或显式 service 依赖至少提供一种")
        self.db = db
        self.datahub_service = datahub_service or DatahubService(db)  # type: ignore[arg-type]
        self.watchlist_service = watchlist_service or DatahubWatchlistService(db)  # type: ignore[arg-type]

    def get_readiness(self, *, as_of_date: date | None = None) -> DailyBriefReadinessInfo:
        target_date = as_of_date or date.today()
        heartbeat = self.datahub_service.get_worker_heartbeat()
        board = self.watchlist_service.get_board(limit_days=10)
        latest_trade_date = self._latest_trade_date(board)
        missing_count = sum(1 for row in board.rows if not row.has_data)
        warnings: list[str] = []

        worker_online = bool(heartbeat and heartbeat.is_online)
        if not worker_online:
            warnings.append("Worker 未在线，更新任务可能不会被消费")
        if not board.rows:
            warnings.append("自选股为空，无法生成个股观察")
        if missing_count > 0:
            warnings.append(f"自选股中有 {missing_count} 个标的缺少日线数据")

        status = self._resolve_status(
            worker_online=worker_online,
            watchlist_count=len(board.rows),
            missing_count=missing_count,
        )
        return DailyBriefReadinessInfo(
            as_of_date=target_date,
            status=status,
            latest_trade_date=latest_trade_date,
            watchlist_count=len(board.rows),
            missing_count=missing_count,
            worker_online=worker_online,
            warnings=warnings,
        )

    def prepare_today_data(self, *, window_days: int = 7) -> DailyBriefPrepareResultInfo:
        run = self.datahub_service.create_daily_incremental_job(
            TriggerDailyIncrementalRequest(dataset="market_daily", window_days=window_days),
            trigger_source="daily_brief",
        )
        return DailyBriefPrepareResultInfo(
            created_runs=1,
            runs=[run],
            message="已提交日线行情增量任务，请在运行监控查看进度",
        )

    def get_today_context(self, *, as_of_date: date | None = None) -> DailyBriefContextInfo:
        target_date = as_of_date or date.today()
        board = self.watchlist_service.get_board(limit_days=10)
        readiness = self.get_readiness(as_of_date=target_date)
        watchlist = [self._to_watchlist_item(row, readiness.latest_trade_date) for row in board.rows]
        risk_flags = self._build_risk_flags(watchlist)
        return DailyBriefContextInfo(
            as_of_date=target_date,
            readiness=readiness,
            market=DailyBriefMarketInfo(),
            related_sectors=self._build_sector_summary(board.rows),
            watchlist=watchlist,
            portfolio=None,
            observations=[],
            risk_flags=risk_flags,
            data_quality=self._build_data_quality(readiness),
        )

    @staticmethod
    def _resolve_status(*, worker_online: bool, watchlist_count: int, missing_count: int) -> str:
        if not worker_online:
            return "worker_offline"
        if watchlist_count == 0:
            return "empty_watchlist"
        if missing_count > 0:
            return "partial"
        return "ready"

    @staticmethod
    def _latest_trade_date(board: WatchlistBoardResponse) -> date | None:
        values = [row.trade_date for row in board.rows if row.trade_date is not None]
        return max(values) if values else None

    @staticmethod
    def _to_watchlist_item(
        row: WatchlistBoardRow,
        latest_trade_date: Optional[date],
    ) -> DailyBriefWatchlistItemInfo:
        data_status = "missing"
        if row.has_data:
            data_status = "latest" if row.trade_date == latest_trade_date else "stale"
        return DailyBriefWatchlistItemInfo(
            symbol=row.symbol,
            name=row.name,
            sector_name=row.sector_name,
            trade_date=row.trade_date,
            close=row.close,
            change_pct=row.change_pct,
            sector_change_pct=row.sector_change_pct,
            volume=row.volume,
            turnover_rate=row.turnover_rate,
            has_data=row.has_data,
            data_status=data_status,
        )

    @staticmethod
    def _build_sector_summary(rows: list[WatchlistBoardRow]) -> list[DailyBriefSectorInfo]:
        grouped: dict[str, list[WatchlistBoardRow]] = defaultdict(list)
        for row in rows:
            if row.sector_name:
                grouped[row.sector_name].append(row)

        sectors: list[DailyBriefSectorInfo] = []
        for sector_name, sector_rows in grouped.items():
            changes = [row.change_pct for row in sector_rows if row.change_pct is not None]
            sector_changes = [row.sector_change_pct for row in sector_rows if row.sector_change_pct is not None]
            sectors.append(
                DailyBriefSectorInfo(
                    sector_name=sector_name,
                    stock_count=len(sector_rows),
                    avg_stock_change_pct=round(sum(changes) / len(changes), 2) if changes else None,
                    sector_change_pct=round(sum(sector_changes) / len(sector_changes), 2) if sector_changes else None,
                )
            )
        return sorted(sectors, key=lambda item: item.sector_change_pct or item.avg_stock_change_pct or 0, reverse=True)

    @staticmethod
    def _build_risk_flags(items: list[DailyBriefWatchlistItemInfo]) -> list[DailyBriefRiskFlagInfo]:
        flags: list[DailyBriefRiskFlagInfo] = []
        for item in items:
            if item.data_status == "missing":
                flags.append(
                    DailyBriefRiskFlagInfo(
                        level="warning",
                        source="data_quality",
                        symbol=item.symbol,
                        message=f"{item.symbol} 缺少最近日线数据",
                    )
                )
            elif item.data_status == "stale":
                flags.append(
                    DailyBriefRiskFlagInfo(
                        level="warning",
                        source="data_quality",
                        symbol=item.symbol,
                        message=f"{item.symbol} 数据不是当前自选股最新交易日",
                    )
                )
        return flags

    @staticmethod
    def _build_data_quality(readiness: DailyBriefReadinessInfo) -> dict[str, str]:
        market_daily = "ok"
        if readiness.missing_count > 0:
            market_daily = "partial"
        if readiness.watchlist_count == 0:
            market_daily = "unknown"
        return {
            "market_daily": market_daily,
            "sector_members": "partial",
            "money_flow": "partial",
        }
