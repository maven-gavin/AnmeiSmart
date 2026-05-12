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
