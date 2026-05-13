from datetime import date
from typing import Any

from app.core.api import BusinessException, ErrorCode
from app.datahub.normalize import normalize_symbol
from app.datahub.providers.base import BaseProvider


class EastMoneyProvider(BaseProvider):
    """基于 akshare 东方财富接口的 market_daily Provider。"""

    provider_name = "eastmoney"

    def get_daily_bars(self, symbol: str, start_date: date, end_date: date) -> list[dict[str, Any]]:
        ak = self._import_akshare()
        normalized_symbol = normalize_symbol(symbol)
        em_symbol = self._to_eastmoney_symbol(normalized_symbol)
        try:
            frame = ak.stock_zh_a_hist(
                symbol=em_symbol,
                period="daily",
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                adjust="qfq",
            )
        except Exception as exc:
            raise BusinessException(
                f"eastmoney 查询失败: {exc}",
                code=ErrorCode.NETWORK_ERROR,
            ) from exc

        if frame is None or frame.empty:
            return []

        rows: list[dict[str, Any]] = []
        for item in frame.to_dict("records"):
            trade_date_value = item.get("日期")
            if trade_date_value is None:
                continue
            trade_date = trade_date_value.date() if hasattr(trade_date_value, "date") else date.fromisoformat(str(trade_date_value))
            rows.append(
                {
                    "symbol": normalized_symbol,
                    "trade_date": trade_date,
                    "open": self._to_float(item.get("开盘")),
                    "high": self._to_float(item.get("最高")),
                    "low": self._to_float(item.get("最低")),
                    "close": self._to_float(item.get("收盘")),
                    "volume": self._to_float(item.get("成交量")),
                    "amount": self._to_float(item.get("成交额")),
                    "turnover_rate": self._to_float(item.get("换手率")),
                }
            )
        return rows

    @staticmethod
    def _to_eastmoney_symbol(symbol: str) -> str:
        if "." not in symbol:
            raise BusinessException(f"证券代码格式错误: {symbol}", code=ErrorCode.VALIDATION_ERROR)
        code, market = symbol.split(".", 1)
        market_upper = market.upper()
        if market_upper not in {"SH", "SZ"}:
            raise BusinessException(f"不支持的交易所代码: {symbol}", code=ErrorCode.VALIDATION_ERROR)
        return code

    @staticmethod
    def _to_float(value: Any) -> float:
        if value is None or value == "":
            return 0.0
        return float(value)

    @staticmethod
    def _import_akshare():
        try:
            import akshare as ak
        except ModuleNotFoundError as exc:  # pragma: no cover
            missing = getattr(exc, "name", None) or str(exc)
            raise BusinessException(
                "缺少 akshare 依赖，无法使用 eastmoney Provider",
                code=ErrorCode.SYSTEM_ERROR,
                details={"missing_module": missing},
            ) from exc
        except Exception as exc:  # pragma: no cover
            raise BusinessException(
                f"加载 akshare 失败: {exc}",
                code=ErrorCode.SYSTEM_ERROR,
                details={"error": str(exc)},
            ) from exc
        return ak
