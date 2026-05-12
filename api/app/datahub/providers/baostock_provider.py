from datetime import date, datetime
from typing import Any

from app.core.api import BusinessException, ErrorCode
from app.datahub.providers.base import BaseProvider
from app.datahub.normalize import normalize_symbol


class BaoStockProvider(BaseProvider):
    provider_name = "baostock"

    def get_daily_bars(self, symbol: str, start_date: date, end_date: date) -> list[dict[str, Any]]:
        bs = self._import_baostock()
        bs_symbol = self._to_baostock_symbol(symbol)
        self._login(bs)
        try:
            query_result = bs.query_history_k_data_plus(
                bs_symbol,
                "date,code,open,high,low,close,volume,amount,turn",
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                frequency="d",
                adjustflag="2",
            )
            if query_result.error_code != "0":
                raise BusinessException(
                    f"baostock 查询失败: {query_result.error_msg}",
                    code=ErrorCode.NETWORK_ERROR,
                )

            rows: list[dict[str, Any]] = []
            while query_result.next():
                record = query_result.get_row_data()
                rows.append(
                    {
                        "symbol": normalize_symbol(symbol),
                        "trade_date": datetime.strptime(record[0], "%Y-%m-%d").date(),
                        "open": self._to_float(record[2]),
                        "high": self._to_float(record[3]),
                        "low": self._to_float(record[4]),
                        "close": self._to_float(record[5]),
                        "volume": self._to_float(record[6]),
                        "amount": self._to_float(record[7]),
                        "turnover_rate": self._to_float(record[8]),
                    }
                )
            return rows
        finally:
            bs.logout()

    def get_security_master(self) -> list[dict[str, Any]]:
        bs = self._import_baostock()
        self._login(bs)
        try:
            query_result = bs.query_all_stock(day=date.today().strftime("%Y-%m-%d"))
            if query_result.error_code != "0":
                raise BusinessException(
                    f"baostock 查询证券主数据失败: {query_result.error_msg}",
                    code=ErrorCode.NETWORK_ERROR,
                )
            rows: list[dict[str, Any]] = []
            while query_result.next():
                record = query_result.get_row_data()
                code = record[0] if len(record) > 0 else ""
                rows.append(
                    {
                        "symbol": self._from_baostock_symbol(code),
                        "exchange": self._exchange_from_baostock_symbol(code),
                        "name": record[1] if len(record) > 1 else "",
                        "list_date": self._to_optional_date(record[3] if len(record) > 3 else ""),
                        "delist_date": self._to_optional_date(record[4] if len(record) > 4 else ""),
                        "status": "active" if (record[2] if len(record) > 2 else "1") == "1" else "inactive",
                        "industry": None,
                        "source_provider": self.provider_name,
                    }
                )
            return rows
        finally:
            bs.logout()

    def get_trading_calendar(self, start_date: date, end_date: date) -> list[dict[str, Any]]:
        bs = self._import_baostock()
        self._login(bs)
        try:
            query_result = bs.query_trade_dates(
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
            )
            if query_result.error_code != "0":
                raise BusinessException(
                    f"baostock 查询交易日历失败: {query_result.error_msg}",
                    code=ErrorCode.NETWORK_ERROR,
                )

            rows: list[dict[str, Any]] = []
            while query_result.next():
                record = query_result.get_row_data()
                trade_date = self._to_optional_date(record[0] if len(record) > 0 else "")
                if trade_date is None:
                    continue
                rows.append(
                    {
                        "exchange": "SSE",
                        "trade_date": trade_date,
                        "is_open": (record[1] if len(record) > 1 else "0") == "1",
                        "previous_trade_date": self._to_optional_date(record[2] if len(record) > 2 else ""),
                        "next_trade_date": None,
                        "source_provider": self.provider_name,
                    }
                )
            return rows
        finally:
            bs.logout()

    @staticmethod
    def _to_baostock_symbol(symbol: str) -> str:
        normalized = normalize_symbol(symbol)
        if "." not in normalized:
            raise BusinessException(f"证券代码格式错误: {symbol}", code=ErrorCode.VALIDATION_ERROR)
        code, market = normalized.split(".", 1)
        market_lower = market.lower()
        if market_lower == "sz":
            return f"sz.{code}"
        if market_lower == "sh":
            return f"sh.{code}"
        raise BusinessException(f"不支持的交易所代码: {symbol}", code=ErrorCode.VALIDATION_ERROR)

    @staticmethod
    def _to_float(value: str) -> float:
        if value == "" or value is None:
            return 0.0
        return float(value)

    @staticmethod
    def _import_baostock():
        try:
            import baostock as bs
        except ModuleNotFoundError as exc:  # pragma: no cover
            missing = getattr(exc, "name", None) or str(exc)
            raise BusinessException(
                "缺少数据采集依赖（baostock / pandas 等）。请在 api 目录执行: pip install -r requirements.txt",
                code=ErrorCode.SYSTEM_ERROR,
                details={"missing_module": missing},
            ) from exc
        except Exception as exc:  # pragma: no cover
            raise BusinessException(
                f"加载 baostock 失败: {exc}",
                code=ErrorCode.SYSTEM_ERROR,
                details={"error": str(exc)},
            ) from exc
        return bs

    @staticmethod
    def _login(bs) -> None:
        login_result = bs.login()
        if login_result.error_code != "0":
            raise BusinessException(
                f"baostock 登录失败: {login_result.error_msg}",
                code=ErrorCode.NETWORK_ERROR,
            )

    @staticmethod
    def _from_baostock_symbol(symbol: str) -> str:
        if "." not in symbol:
            return normalize_symbol(symbol)
        market, code = symbol.split(".", 1)
        market = market.lower()
        if market == "sz":
            return f"{code}.SZ"
        if market == "sh":
            return f"{code}.SH"
        return normalize_symbol(symbol)

    @staticmethod
    def _exchange_from_baostock_symbol(symbol: str) -> str:
        if symbol.lower().startswith("sz."):
            return "SZSE"
        if symbol.lower().startswith("sh."):
            return "SSE"
        return "UNKNOWN"

    @staticmethod
    def _to_optional_date(value: str | None) -> date | None:
        if not value:
            return None
        return datetime.strptime(value, "%Y-%m-%d").date()
