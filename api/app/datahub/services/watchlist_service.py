from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core.api import BusinessException, ErrorCode
from app.datahub.catalog import get_dataset_label
from app.datahub.models import DatahubDatasetWatermark, DatahubObjectIndex, DatahubQualityReport, DatahubWatchlistItem
from app.datahub.normalize import normalize_symbol
from app.datahub.providers import BaoStockProvider
from app.datahub.schemas.datahub import (
    DatahubWatchlistCreate,
    DatahubWatchlistInfo,
    DatahubWatchlistSymbolSummary,
    DatahubWatchlistUpdate,
    DatahubWatchlistWatermarkInfo,
    WatchlistBoardResponse,
    WatchlistBoardRow,
)
from app.datahub.services.market_daily_read_service import MarketDailyReadService
from app.datahub.services.sector_members_read_service import SectorMembersReadService
from app.datahub.services.security_master_read_service import SecurityMasterReadService


class DatahubWatchlistService:
    def __init__(self, db: Session):
        self.db = db

    def list_items(self) -> list[DatahubWatchlistInfo]:
        rows = (
            self.db.query(DatahubWatchlistItem)
            .order_by(DatahubWatchlistItem.sort_order.asc(), DatahubWatchlistItem.created_at.asc())
            .all()
        )
        name_map = self._load_security_name_map()
        changed = False
        for row in rows:
            if self._apply_resolved_name(row, name_map):
                changed = True
        if changed:
            self.db.commit()
        return [self._to_info(row) for row in rows]

    def add_item(self, payload: DatahubWatchlistCreate) -> DatahubWatchlistInfo:
        symbol = normalize_symbol(payload.symbol)
        if not symbol:
            raise BusinessException("证券代码不能为空", code=ErrorCode.VALIDATION_ERROR)

        existing = self.db.query(DatahubWatchlistItem).filter(DatahubWatchlistItem.symbol == symbol).first()
        if existing:
            raise BusinessException(f"自选股已存在: {symbol}", code=ErrorCode.VALIDATION_ERROR)

        name = (payload.name or "").strip() or None
        if self._is_placeholder_name(name):
            name = self._lookup_security_name(symbol)

        max_sort = self.db.query(DatahubWatchlistItem.sort_order).order_by(DatahubWatchlistItem.sort_order.desc()).first()
        next_sort = (max_sort[0] if max_sort else -1) + 1
        row = DatahubWatchlistItem(
            symbol=symbol,
            name=name,
            sort_order=next_sort,
            note=(payload.note or "").strip() or None,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return self._to_info(row)

    def update_item(self, item_id: str, payload: DatahubWatchlistUpdate) -> DatahubWatchlistInfo:
        row = self.db.query(DatahubWatchlistItem).filter(DatahubWatchlistItem.id == item_id).first()
        if row is None:
            raise BusinessException("自选股不存在", code=ErrorCode.NOT_FOUND)

        data = payload.model_dump(exclude_unset=True)
        if "name" in data:
            row.name = (data["name"] or "").strip() or None
        if "note" in data:
            row.note = (data["note"] or "").strip() or None

        self.db.commit()
        self.db.refresh(row)
        return self._to_info(row)

    def delete_item(self, item_id: str) -> None:
        row = self.db.query(DatahubWatchlistItem).filter(DatahubWatchlistItem.id == item_id).first()
        if row is None:
            raise BusinessException("自选股不存在", code=ErrorCode.NOT_FOUND)
        self.db.delete(row)
        self.db.commit()

    def get_symbol_summary(self, symbol: str) -> DatahubWatchlistSymbolSummary:
        normalized = normalize_symbol(symbol)
        item = self.db.query(DatahubWatchlistItem).filter(DatahubWatchlistItem.symbol == normalized).first()
        if item and not item.name:
            resolved = self._lookup_security_name(normalized)
            if resolved:
                item.name = resolved
                self.db.commit()
                self.db.refresh(item)

        object_rows = (
            self.db.query(DatahubObjectIndex)
            .filter(DatahubObjectIndex.symbol == normalized)
            .order_by(DatahubObjectIndex.end_date.desc().nullslast(), DatahubObjectIndex.created_at.desc())
            .limit(20)
            .all()
        )
        watermark_rows = (
            self.db.query(DatahubDatasetWatermark)
            .filter(DatahubDatasetWatermark.symbol == normalized)
            .order_by(DatahubDatasetWatermark.dataset.asc())
            .all()
        )
        quality_rows = (
            self.db.query(DatahubQualityReport)
            .filter(DatahubQualityReport.symbol == normalized)
            .order_by(DatahubQualityReport.checked_at.desc())
            .limit(10)
            .all()
        )

        market_daily = next((row for row in object_rows if row.dataset == "market_daily"), None)
        latest_quality = quality_rows[0] if quality_rows else None

        return DatahubWatchlistSymbolSummary(
            symbol=normalized,
            name=item.name if item else self._lookup_security_name(normalized),
            market_daily_start_date=market_daily.start_date if market_daily else None,
            market_daily_end_date=market_daily.end_date if market_daily else None,
            market_daily_row_count=market_daily.row_count if market_daily else 0,
            market_daily_quality_score=market_daily.quality_score if market_daily else None,
            latest_quality_score=latest_quality.quality_score if latest_quality else None,
            latest_quality_severity=latest_quality.severity if latest_quality else None,
            watermarks=[
                DatahubWatchlistWatermarkInfo(
                    dataset=row.dataset,
                    dataset_label=get_dataset_label(row.dataset),
                    last_success_date=row.last_success_date,
                    last_quality_score=row.last_quality_score,
                )
                for row in watermark_rows
            ],
            object_indexes=[
                {
                    "dataset": row.dataset,
                    "dataset_label": get_dataset_label(row.dataset),
                    "start_date": row.start_date.isoformat() if row.start_date else None,
                    "end_date": row.end_date.isoformat() if row.end_date else None,
                    "row_count": row.row_count,
                    "quality_score": row.quality_score,
                    "object_key": row.object_key,
                }
                for row in object_rows
            ],
            quality_reports=[
                {
                    "dataset": row.dataset,
                    "dataset_label": get_dataset_label(row.dataset),
                    "biz_date": row.biz_date.isoformat() if row.biz_date else None,
                    "quality_score": row.quality_score,
                    "severity": row.severity,
                    "checked_at": row.checked_at.isoformat() if row.checked_at else None,
                }
                for row in quality_rows
            ],
        )

    def _load_security_name_map(self) -> dict[str, str]:
        name_map = SecurityMasterReadService(self.db).get_name_map()
        if name_map:
            return name_map
        try:
            rows = BaoStockProvider().get_security_master(day=date.today())
        except Exception:
            return {}
        result: dict[str, str] = {}
        for row in rows:
            symbol = normalize_symbol(str(row.get("symbol") or ""))
            name = str(row.get("name") or "").strip()
            if symbol and name:
                result[symbol] = name
        return result

    def _lookup_security_name(self, symbol: str) -> str | None:
        return self._load_security_name_map().get(normalize_symbol(symbol))

    def get_board(self, *, limit_days: int = 30) -> WatchlistBoardResponse:
        items = self.list_items()
        name_map = self._load_security_name_map()
        reader = MarketDailyReadService(self.db)
        sector_reader = SectorMembersReadService(self.db)
        symbol_sector_map = sector_reader.get_symbol_sector_map()
        end_date = date.today()
        start_date = end_date - timedelta(days=max(limit_days - 1, 0))
        rows: list[WatchlistBoardRow] = []
        board_trade_date: date | None = None
        needed_sector_codes: set[str] = set()

        for item in items:
            bars = reader.get_bars(symbol=item.symbol, start_date=start_date, end_date=end_date)
            latest = bars[-1] if bars else None
            previous = bars[-2] if len(bars) >= 2 else None
            change_amount = None
            change_pct = None
            if latest and previous and previous["close"]:
                change_amount = round(latest["close"] - previous["close"], 4)
                change_pct = round((change_amount / previous["close"]) * 100, 2)

            trade_date_value = None
            if latest and latest.get("trade_date"):
                td = latest["trade_date"]
                if isinstance(td, date):
                    trade_date_value = td
                else:
                    trade_date_value = date.fromisoformat(str(td)[:10])
                if board_trade_date is None or trade_date_value > board_trade_date:
                    board_trade_date = trade_date_value

            sector_info = symbol_sector_map.get(item.symbol)
            sector_name = sector_info["sector_name"] if sector_info else None
            sector_code = sector_info["sector_code"] if sector_info else None
            if sector_code:
                needed_sector_codes.add(sector_code)

            display_name = self._resolve_display_name(item.symbol, item.name, name_map)

            rows.append(
                WatchlistBoardRow(
                    id=item.id,
                    symbol=item.symbol,
                    name=display_name,
                    sector_name=sector_name,
                    trade_date=trade_date_value,
                    open=latest["open"] if latest else None,
                    high=latest["high"] if latest else None,
                    low=latest["low"] if latest else None,
                    close=latest["close"] if latest else None,
                    change_amount=change_amount,
                    change_pct=change_pct,
                    sector_change_pct=None,
                    volume=latest["volume"] if latest else None,
                    turnover_rate=latest.get("turnover_rate") if latest else None,
                    has_data=latest is not None,
                )
            )

        sector_change_map = sector_reader.compute_sector_change_map(
            trade_date=board_trade_date,
            market_reader=reader,
            sector_codes=needed_sector_codes,
        )
        if sector_change_map:
            enriched: list[WatchlistBoardRow] = []
            for row in rows:
                sector_info = symbol_sector_map.get(row.symbol)
                sector_code = sector_info["sector_code"] if sector_info else None
                sector_change_pct = sector_change_map.get(sector_code) if sector_code else None
                enriched.append(row.model_copy(update={"sector_change_pct": sector_change_pct}))
            rows = enriched

        return WatchlistBoardResponse(limit_days=limit_days, rows=rows)

    @staticmethod
    def _is_placeholder_name(name: str | None) -> bool:
        if not name:
            return True
        trimmed = name.strip()
        return not trimmed or trimmed.isdigit()

    def _resolve_display_name(self, symbol: str, stored_name: str | None, name_map: dict[str, str]) -> str | None:
        resolved = name_map.get(normalize_symbol(symbol))
        if resolved:
            return resolved
        if stored_name and not self._is_placeholder_name(stored_name):
            return stored_name
        return None

    @staticmethod
    def _apply_resolved_name(row: DatahubWatchlistItem, name_map: dict[str, str]) -> bool:
        resolved = name_map.get(row.symbol)
        if not resolved:
            return False
        if row.name and not DatahubWatchlistService._is_placeholder_name(row.name):
            return False
        row.name = resolved
        return True

    @staticmethod
    def _to_info(row: DatahubWatchlistItem) -> DatahubWatchlistInfo:
        return DatahubWatchlistInfo(
            id=row.id,
            symbol=row.symbol,
            name=row.name,
            sort_order=row.sort_order,
            note=row.note,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
