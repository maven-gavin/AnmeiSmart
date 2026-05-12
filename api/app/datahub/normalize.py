def normalize_symbol(symbol: str) -> str:
    """统一证券代码格式，第一阶段先做基础规整。"""
    return symbol.strip().upper()
