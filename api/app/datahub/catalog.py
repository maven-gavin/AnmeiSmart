from typing import Final

CORE_DATASETS: Final[list[str]] = [
    "trading_calendar",
    "security_master",
    "market_daily",
]

EXTENDED_DATASETS: Final[list[str]] = [
    "money_flow",
    "sector_members",
    "financial_summary",
]

ALL_DATASETS: Final[list[str]] = CORE_DATASETS + EXTENDED_DATASETS

DATASET_LABELS: Final[dict[str, str]] = {
    "trading_calendar": "交易日历",
    "security_master": "证券主数据",
    "market_daily": "日线行情",
    "money_flow": "资金流向",
    "sector_members": "板块成分",
    "financial_summary": "财务摘要",
}


def get_dataset_label(dataset_key: str) -> str:
    return DATASET_LABELS.get(dataset_key, dataset_key)
