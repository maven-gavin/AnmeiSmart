def normalize_symbol(symbol: str) -> str:
    """统一证券代码格式，支持 6 位纯数字自动补全交易所后缀。"""
    normalized = symbol.strip().upper()
    if "." not in normalized and normalized.isdigit() and len(normalized) == 6:
        if normalized.startswith(("6", "9")):
            return f"{normalized}.SH"
        if normalized.startswith(("0", "3")):
            return f"{normalized}.SZ"
    return normalized
