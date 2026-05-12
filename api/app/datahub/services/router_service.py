from app.datahub.catalog import CORE_DATASETS


class DatahubRouterService:
    """Provider 路由策略服务（第一阶段简化版）。"""

    def get_provider_priority(self, dataset: str) -> list[str]:
        if dataset == "market_daily":
            return ["baostock", "eastmoney", "minio_cache"]
        if dataset in CORE_DATASETS:
            return ["eastmoney", "baostock", "minio_cache"]
        return ["baostock", "minio_cache"]
