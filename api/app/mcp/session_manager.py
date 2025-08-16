"""
MCP 会话管理

提供基于 Redis 的会话令牌签发与校验能力
"""

from __future__ import annotations

import json
import uuid
from typing import Optional, Dict, Any

from app.core.config import get_settings
from app.core.redis_client import get_redis_client


SESSION_PREFIX = "mcp:session:"
AUTH_CODE_PREFIX = "mcp:authcode:"


async def issue_session_token(
    group_info: Dict[str, Any],
    client_name: str = "dify",
    allowed_tools: Optional[list[str]] = None,
) -> str:
    """签发会话令牌并写入 Redis（带 TTL）"""
    settings = get_settings()
    token = f"mcp_sess_{uuid.uuid4().hex}"

    session_data = {
        "group_id": group_info.get("id"),
        "group_name": group_info.get("name"),
        "client": client_name,
        "allowed_tools": allowed_tools or [],
    }

    redis = await get_redis_client()
    key = SESSION_PREFIX + token
    await redis.set(key, json.dumps(session_data), ex=settings.MCP_SESSION_TTL_SECONDS)
    return token


async def validate_session_token(token: str) -> Optional[Dict[str, Any]]:
    """校验会话令牌，返回会话数据（不存在或过期返回 None）"""
    if not token:
        return None
    redis = await get_redis_client()
    data = await redis.get(SESSION_PREFIX + token)
    if not data:
        return None
    try:
        if isinstance(data, (bytes, bytearray)):
            data = data.decode('utf-8')
        return json.loads(data)
    except Exception:
        return None


async def revoke_session_token(token: str) -> None:
    """吊销会话令牌"""
    redis = await get_redis_client()
    await redis.delete(SESSION_PREFIX + token)


async def save_auth_code_mapping(auth_code: str, data: Dict[str, Any], ttl_seconds: int = 600) -> None:
    """保存授权码映射（带TTL）"""
    redis = await get_redis_client()
    await redis.set(AUTH_CODE_PREFIX + auth_code, json.dumps(data), ex=ttl_seconds)


async def consume_auth_code(auth_code: str) -> Optional[Dict[str, Any]]:
    """一次性消费授权码，返回数据并删除键"""
    redis = await get_redis_client()
    key = AUTH_CODE_PREFIX + auth_code
    data = await redis.get(key)
    if not data:
        return None
    await redis.delete(key)
    try:
        return json.loads(data)
    except Exception:
        return None


