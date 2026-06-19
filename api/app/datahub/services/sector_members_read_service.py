from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.datahub.normalize import normalize_symbol
from app.datahub.services.market_daily_read_service import MarketDailyReadService
from app.datahub.services.snapshot_read_service import SnapshotDatasetReadService


class SectorMembersReadService:
    MAX_MEMBERS_FOR_CHANGE = 40

    def __init__(self, db: Session):
        self.db = db
        self._reader = SnapshotDatasetReadService(db, "sector_members")

    def get_symbol_sector_map(self) -> dict[str, dict[str, str]]:
        result: dict[str, dict[str, str]] = {}
        for row in self._reader.load_rows():
            symbol = normalize_symbol(str(row.get("symbol") or ""))
            if not symbol:
                continue
            sector_code = str(row.get("sector_code") or "").strip()
            sector_name = str(row.get("sector_name") or sector_code).strip()
            if not sector_code and not sector_name:
                continue
            result[symbol] = {
                "sector_code": sector_code or sector_name,
                "sector_name": sector_name or sector_code,
            }
        return result

    def get_sector_symbols_map(self) -> dict[str, list[str]]:
        grouped: dict[str, list[str]] = defaultdict(list)
        for symbol, info in self.get_symbol_sector_map().items():
            sector_code = info["sector_code"]
            if sector_code not in grouped[sector_code]:
                grouped[sector_code].append(symbol)
        return dict(grouped)

    def compute_sector_change_map(
        self,
        *,
        trade_date: date | None,
        market_reader: MarketDailyReadService,
        sector_codes: set[str] | None = None,
    ) -> dict[str, float]:
        if trade_date is None:
            return {}
        if sector_codes is not None and len(sector_codes) == 0:
            return {}

        sector_symbols = self.get_sector_symbols_map()
        start_date = trade_date - timedelta(days=10)
        result: dict[str, float] = {}
        targets = sector_codes if sector_codes is not None else set(sector_symbols.keys())

        for sector_code in targets:
            members = sector_symbols.get(sector_code, [])
            if not members:
                continue
            changes: list[float] = []
            for symbol in members[: self.MAX_MEMBERS_FOR_CHANGE]:
                bars = market_reader.get_bars(symbol=symbol, start_date=start_date, end_date=trade_date)
                if len(bars) < 2:
                    continue
                latest = bars[-1]
                latest_date = latest["trade_date"]
                if isinstance(latest_date, str):
                    latest_date = date.fromisoformat(latest_date[:10])
                elif not isinstance(latest_date, date):
                    continue
                if latest_date != trade_date:
                    continue
                previous = bars[-2]
                prev_close = float(previous.get("close") or 0)
                if not prev_close:
                    continue
                change_pct = (float(latest.get("close") or 0) - prev_close) / prev_close * 100
                changes.append(change_pct)
            if changes:
                result[sector_code] = round(sum(changes) / len(changes), 2)
        return result
