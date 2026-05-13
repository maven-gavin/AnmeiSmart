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

    def get_money_flow(self, symbol: str, start_date: date, end_date: date) -> list[dict[str, Any]]:
        ak = self._import_akshare()
        normalized_symbol = normalize_symbol(symbol)
        stock, market = self._to_stock_and_market(normalized_symbol)
        try:
            frame = ak.stock_individual_fund_flow(stock=stock, market=market)
        except Exception as exc:
            raise BusinessException(
                f"eastmoney 资金流查询失败: {exc}",
                code=ErrorCode.NETWORK_ERROR,
            ) from exc
        if frame is None or frame.empty:
            return []

        rows: list[dict[str, Any]] = []
        for item in frame.to_dict("records"):
            trade_date_raw = self._pick(item, "日期", "trade_date")
            trade_date = self._to_date(trade_date_raw)
            if trade_date is None or trade_date < start_date or trade_date > end_date:
                continue
            rows.append(
                {
                    "symbol": normalized_symbol,
                    "trade_date": trade_date,
                    "main_net_inflow": self._to_float(self._pick(item, "主力净流入-净额", "主力净流入净额")),
                    "large_net_inflow": self._to_float(self._pick(item, "超大单净流入-净额", "大单净流入-净额")),
                    "medium_net_inflow": self._to_float(self._pick(item, "中单净流入-净额")),
                    "small_net_inflow": self._to_float(self._pick(item, "小单净流入-净额")),
                }
            )
        return rows

    def get_sector_list(self) -> list[dict[str, Any]]:
        ak = self._import_akshare()
        try:
            frame = ak.stock_board_industry_name_em()
        except Exception as exc:
            raise BusinessException(
                f"eastmoney 行业板块列表查询失败: {exc}",
                code=ErrorCode.NETWORK_ERROR,
            ) from exc
        if frame is None or frame.empty:
            return []
        rows: list[dict[str, Any]] = []
        for item in frame.to_dict("records"):
            name = str(self._pick(item, "板块名称", "name") or "").strip()
            if not name:
                continue
            code = str(self._pick(item, "板块代码", "code") or name).strip()
            rows.append({"sector_code": code, "sector_name": name})
        return rows

    def get_sector_members(self, sector_code: str, asof_date: date | None = None) -> list[dict[str, Any]]:
        ak = self._import_akshare()
        try:
            frame = ak.stock_board_industry_cons_em(symbol=sector_code)
        except Exception as exc:
            raise BusinessException(
                f"eastmoney 板块成分查询失败: {exc}",
                code=ErrorCode.NETWORK_ERROR,
            ) from exc
        if frame is None or frame.empty:
            return []
        snapshot_date = asof_date or date.today()
        rows: list[dict[str, Any]] = []
        for item in frame.to_dict("records"):
            code = str(self._pick(item, "代码", "symbol") or "").strip()
            name = str(self._pick(item, "名称", "name") or "").strip()
            if not code:
                continue
            exchange = "SH" if code.startswith("6") else "SZ"
            rows.append(
                {
                    "sector_code": sector_code,
                    "sector_name": sector_code,
                    "symbol": normalize_symbol(f"{code}.{exchange}"),
                    "member_name": name,
                    "asof_date": snapshot_date,
                }
            )
        return rows

    def get_financial_statement(self, symbol: str, start_date: date, end_date: date) -> list[dict[str, Any]]:
        ak = self._import_akshare()
        normalized_symbol = normalize_symbol(symbol)
        code = self._to_eastmoney_symbol(normalized_symbol)
        try:
            frame = ak.stock_financial_abstract(symbol=code)
        except Exception as exc:
            raise BusinessException(
                f"eastmoney 财务摘要查询失败: {exc}",
                code=ErrorCode.NETWORK_ERROR,
            ) from exc
        if frame is None or frame.empty:
            return []

        records: list[dict[str, Any]] = []
        for item in frame.to_dict("records"):
            report_date = self._to_date(self._pick(item, "报告期", "report_date"))
            if report_date is None or report_date < start_date or report_date > end_date:
                continue
            pub_date = self._to_date(self._pick(item, "公告日期", "最新公告日期")) or report_date
            for key, value in item.items():
                if key in {"选项", "报告期", "公告日期", "最新公告日期"}:
                    continue
                records.append(
                    {
                        "symbol": normalized_symbol,
                        "report_date": report_date,
                        "pub_date": pub_date,
                        "metric_name": str(key),
                        "metric_value": self._to_float(value),
                        "metric_group": "financial_abstract",
                    }
                )
        return records

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
    def _to_stock_and_market(symbol: str) -> tuple[str, str]:
        if "." not in symbol:
            raise BusinessException(f"证券代码格式错误: {symbol}", code=ErrorCode.VALIDATION_ERROR)
        code, market = symbol.split(".", 1)
        market_lower = market.lower()
        if market_lower not in {"sh", "sz"}:
            raise BusinessException(f"不支持的交易所代码: {symbol}", code=ErrorCode.VALIDATION_ERROR)
        return code, market_lower

    @staticmethod
    def _to_float(value: Any) -> float:
        if value is None or value == "":
            return 0.0
        value_str = str(value).strip().replace(",", "").replace("%", "")
        if value_str in {"", "-", "--", "nan", "None"}:
            return 0.0
        return float(value_str)

    @staticmethod
    def _to_date(value: Any) -> date | None:
        if value is None:
            return None
        value_str = str(value).strip()
        if not value_str:
            return None
        if hasattr(value, "date"):
            try:
                return value.date()
            except Exception:
                pass
        value_str = value_str.replace("/", "-")
        if len(value_str) == 8 and value_str.isdigit():
            return date.fromisoformat(f"{value_str[0:4]}-{value_str[4:6]}-{value_str[6:8]}")
        return date.fromisoformat(value_str[:10])

    @staticmethod
    def _pick(item: dict[str, Any], *keys: str) -> Any:
        for key in keys:
            if key in item:
                return item[key]
        return None

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
