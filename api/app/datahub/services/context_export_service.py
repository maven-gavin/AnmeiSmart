from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.datahub.normalize import normalize_symbol
from app.datahub.services.daily_brief_service import DailyBriefService
from app.datahub.services.market_daily_read_service import MarketDailyReadService


class ContextExportService:
    """为 AI / opencode 输出稳定、可序列化的 DataHub 上下文。"""

    def __init__(
        self,
        db: Session | None = None,
        daily_brief_service: DailyBriefService | None = None,
        market_daily_read_service: MarketDailyReadService | None = None,
    ):
        if db is None and (daily_brief_service is None or market_daily_read_service is None):
            raise ValueError("db 或显式 service 依赖至少提供一种")
        self.daily_brief_service = daily_brief_service or DailyBriefService(db=db)
        self.market_daily_read_service = market_daily_read_service or MarketDailyReadService(db)  # type: ignore[arg-type]

    def get_daily_context(self, *, as_of_date: date | None = None) -> dict[str, Any]:
        context = self.daily_brief_service.get_today_context(as_of_date=as_of_date)
        return context.model_dump(mode="json")

    def get_opencode_context(self, *, as_of_date: date | None = None) -> dict[str, Any]:
        context = self.get_daily_context(as_of_date=as_of_date)
        return {
            "kind": "datahub.opencode.daily_context",
            "version": "1.0",
            "context": context,
            "usage_hint": "将该 JSON 作为市场、自选股和数据质量上下文，再结合你的实盘截图/OCR和人工备注进行策略分析。",
        }

    def get_symbol_context(self, *, symbol: str, days: int = 10, as_of_date: date | None = None) -> dict[str, Any]:
        normalized = normalize_symbol(symbol)
        end_date = as_of_date or date.today()
        start_date = end_date - timedelta(days=max(days * 2, days))
        bars = self.market_daily_read_service.get_bars(symbol=normalized, start_date=start_date, end_date=end_date)
        recent_bars = bars[-days:] if len(bars) > days else bars
        return {
            "kind": "datahub.symbol_context",
            "version": "1.0",
            "symbol": normalized,
            "as_of_date": end_date.isoformat(),
            "days": days,
            "bars": [
                {
                    **row,
                    "trade_date": row["trade_date"].isoformat() if hasattr(row.get("trade_date"), "isoformat") else row.get("trade_date"),
                }
                for row in recent_bars
            ],
            "data_quality": {
                "market_daily": "ok" if recent_bars else "missing",
            },
        }
