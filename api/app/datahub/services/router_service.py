from app.datahub.catalog import CORE_DATASETS
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
import time
from typing import Callable, TypeVar

from app.core.api import BusinessException, ErrorCode

T = TypeVar("T")

class DatahubRouterService:
    """Provider 路由策略服务（第一阶段简化版）。"""

    DATASET_TIMEOUT_SECONDS = {
        "market_daily": 10,
        "money_flow": 10,
        "sector_members": 15,
        "financial_summary": 15,
        "security_master": 10,
        "trading_calendar": 10,
    }
    RETRY_BACKOFF_SECONDS = [1, 2]

    def get_provider_priority(self, dataset: str) -> list[str]:
        if dataset == "market_daily":
            return ["baostock", "eastmoney", "minio_cache"]
        if dataset in {"money_flow", "sector_members", "financial_summary"}:
            return ["eastmoney", "baostock", "minio_cache"]
        if dataset == "security_master":
            return ["baostock", "eastmoney", "minio_cache"]
        if dataset in CORE_DATASETS:
            return ["eastmoney", "baostock", "minio_cache"]
        return ["baostock", "minio_cache"]

    def run_with_policy(self, *, dataset: str, provider: str, operation: Callable[[], T]) -> T:
        timeout = self.DATASET_TIMEOUT_SECONDS.get(dataset, 10)
        retries = len(self.RETRY_BACKOFF_SECONDS)
        last_error: Exception | None = None
        for attempt in range(retries + 1):
            try:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(operation)
                    return future.result(timeout=timeout)
            except FuturesTimeoutError as exc:
                last_error = BusinessException(
                    f"{provider} {dataset} 请求超时({timeout}s)",
                    code=ErrorCode.NETWORK_ERROR,
                )
            except Exception as exc:  # pragma: no cover
                last_error = exc
            if attempt < retries:
                time.sleep(self.RETRY_BACKOFF_SECONDS[attempt])
        if isinstance(last_error, Exception):
            raise last_error
        raise BusinessException(f"{provider} {dataset} 路由调用失败", code=ErrorCode.SYSTEM_ERROR)
