from typing import Any, Optional


def extract_external_user_id(item: dict[str, Any]) -> Optional[str]:
    """从会话存档单条消息中提取 external_userid（外部联系人ID）"""
    for key in ("external_userid", "external_user_id", "ext_userid"):
        val = item.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()

    candidates: list[str] = []
    from_id = item.get("from")
    if isinstance(from_id, str) and from_id.strip():
        candidates.append(from_id.strip())

    to_list = item.get("tolist") or item.get("to_list")
    if isinstance(to_list, list):
        for to_id in to_list:
            if isinstance(to_id, str) and to_id.strip():
                candidates.append(to_id.strip())

    for cand in candidates:
        if cand.startswith(("wo", "wm")):
            return cand

    return None
