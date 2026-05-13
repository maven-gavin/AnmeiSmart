from abc import ABC, abstractmethod
from datetime import date
from typing import Any, Optional


class BaseProvider(ABC):
    provider_name: str = "base"

    @abstractmethod
    def get_daily_bars(self, symbol: str, start_date: date, end_date: date) -> list[dict[str, Any]]:
        raise NotImplementedError

    def get_money_flow(self, symbol: str, start_date: date, end_date: date) -> list[dict[str, Any]]:
        return []

    def get_sector_list(self) -> list[dict[str, Any]]:
        return []

    def get_sector_members(self, sector_code: str, asof_date: Optional[date] = None) -> list[dict[str, Any]]:
        return []

    def get_financial_statement(self, symbol: str, start_date: date, end_date: date) -> list[dict[str, Any]]:
        return []

    def get_security_master(self, day: Optional[date] = None) -> list[dict[str, Any]]:
        return []

    def get_trading_calendar(self, start_date: date, end_date: date) -> list[dict[str, Any]]:
        return []
