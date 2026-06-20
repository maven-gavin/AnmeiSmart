from datetime import date
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.datahub.schemas.datahub import DatahubJobRunInfo


class DailyBriefReadinessInfo(BaseModel):
    as_of_date: date
    status: str
    latest_trade_date: Optional[date] = None
    watchlist_count: int = 0
    missing_count: int = 0
    worker_online: bool = False
    warnings: list[str] = Field(default_factory=list)


class DailyBriefMarketInfo(BaseModel):
    indices: list[dict[str, Any]] = Field(default_factory=list)
    five_day_trend: str = "unknown"
    turnover_summary: Optional[dict[str, Any]] = None
    breadth: Optional[dict[str, Any]] = None


class DailyBriefSectorInfo(BaseModel):
    sector_name: str
    stock_count: int
    avg_stock_change_pct: Optional[float] = None
    sector_change_pct: Optional[float] = None


class DailyBriefWatchlistItemInfo(BaseModel):
    symbol: str
    name: Optional[str] = None
    sector_name: Optional[str] = None
    trade_date: Optional[date] = None
    close: Optional[float] = None
    change_pct: Optional[float] = None
    sector_change_pct: Optional[float] = None
    volume: Optional[float] = None
    turnover_rate: Optional[float] = None
    has_data: bool = False
    data_status: str = "missing"


class DailyBriefRiskFlagInfo(BaseModel):
    level: str
    source: str
    message: str
    symbol: Optional[str] = None


class DailyBriefContextInfo(BaseModel):
    as_of_date: date
    readiness: DailyBriefReadinessInfo
    market: DailyBriefMarketInfo
    related_sectors: list[DailyBriefSectorInfo] = Field(default_factory=list)
    watchlist: list[DailyBriefWatchlistItemInfo] = Field(default_factory=list)
    portfolio: Optional[dict[str, Any]] = None
    observations: list[dict[str, Any]] = Field(default_factory=list)
    risk_flags: list[DailyBriefRiskFlagInfo] = Field(default_factory=list)
    data_quality: dict[str, str] = Field(default_factory=dict)


class DailyBriefPrepareResultInfo(BaseModel):
    created_runs: int
    runs: list[DatahubJobRunInfo] = Field(default_factory=list)
    message: str
