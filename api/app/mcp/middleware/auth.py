"""
MCP认证中间件

负责API Key认证和权限验证
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging

from app.db.base import get_db
from app.services.mcp_group_service import MCPGroupService
from app.mcp.session_manager import validate_session_token
from app.core.config import get_settings
from app.core.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class MCPAuthenticator:
    """MCP认证器 - 负责API Key认证和权限验证"""
    
    @staticmethod
    async def authenticate_request(api_key: str, db: Session) -> Optional[Dict[str, Any]]:
        """验证API Key并返回分组信息"""
        return await MCPGroupService.validate_api_key(db, api_key)
    
    @staticmethod
    async def check_tool_permission(group_info: Dict[str, Any], tool_name: str, db: Session) -> bool:
        """检查工具访问权限"""
        if not group_info:
            return False
        
        return await MCPGroupService.is_tool_in_group(db, tool_name, group_info["id"])


class MCPMiddleware:
    """MCP中间件 - 负责请求预处理和后处理"""
    
    def __init__(self, authenticator: MCPAuthenticator):
        self.authenticator = authenticator
    
    async def process_request(self, request: Request, call_next):
        """处理MCP请求中间件"""
        if not request.url.path.startswith("/mcp"):
            return await call_next(request)
        
        # OAuth 和发现端点无需认证
        oauth_endpoints = [
            "/mcp/register",
            "/mcp/.well-known/oauth-authorization-server",
            "/mcp/oauth/authorize",
            "/mcp/oauth/authorize/submit",
            "/mcp/oauth/token"
        ]
        
        # JSON-RPC 端点（Dify 兼容）无需中间件认证（内部处理认证）
        jsonrpc_endpoints = [
            "/api/v1/mcp/jsonrpc"
        ]
        
        # 管理员内部端点无需认证
        admin_endpoints = [
            "/mcp/admin/tools/all",
            "/mcp/server/info",
            "/mcp/tools/info",
            "/mcp/health"
        ]
        
        # 合并无需认证的端点
        public_endpoints = oauth_endpoints + jsonrpc_endpoints + admin_endpoints
        
        if request.url.path in public_endpoints:
            return await call_next(request)
        
        # 提取 Bearer token（优先作为 sessionToken 使用）
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(
                {"error": "Missing Authorization header", "code": "UNAUTHORIZED"}, 
                status_code=401
            )
        
        token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else auth_header

        # 优先校验 sessionToken
        session = await validate_session_token(token)
        if session:
            # 会话级速率限制（按方法 + 工具名）
            try:
                settings = get_settings()
                if settings.MCP_RL_ENABLED:
                    import time, json as _json
                    method = None
                    tool_name = "list"
                    try:
                        body = await request.body()
                        if body:
                            payload = _json.loads(body.decode("utf-8"))
                            method = payload.get("method")
                            if method == "tools/call":
                                params = payload.get("params", {})
                                tool_name = params.get("name", "unknown")
                            else:
                                tool_name = "list"
                    except Exception:
                        pass
                    method = method or request.query_params.get("method") or "unknown"
                    window = int(time.time() // settings.MCP_RL_WINDOW_SECONDS)
                    rl_key = f"mcp:rl:{session.get('group_id')}:{token}:{method}:{tool_name}:{window}"
                    limit = settings.MCP_RL_CALL_LIMIT if method == "tools/call" else settings.MCP_RL_LIST_LIMIT
                    redis = await get_redis_client()
                    current = await redis.get(rl_key)
                    if not current:
                        await redis.set(rl_key, "1", ex=settings.MCP_RL_WINDOW_SECONDS)
                    else:
                        try:
                            n = int(current if isinstance(current, str) else current.decode("utf-8"))
                        except Exception:
                            n = 0
                        if n + 1 > limit:
                            return JSONResponse(
                                {"error": "Rate limit exceeded", "code": "RATE_LIMIT", "limit": limit, "window": settings.MCP_RL_WINDOW_SECONDS},
                                status_code=429,
                            )
                        await redis.set(rl_key, str(n + 1), ex=settings.MCP_RL_WINDOW_SECONDS)
            except Exception as e:
                logger.warning(f"速率限制检查失败，跳过限流: {e}")
            request.state.mcp_group = {"id": session.get("group_id"), "name": session.get("group_name")}
            request.state.db = next(get_db())
            return await call_next(request)

        # 兼容：使用 API Key 直接访问（将逐步淘汰）
        db = next(get_db())
        try:
            group_info = await self.authenticator.authenticate_request(token, db)
            if not group_info:
                return JSONResponse(
                    {"error": "Invalid API Key or OAuth Token", "code": "FORBIDDEN"}, 
                    status_code=403
                )
            request.state.mcp_group = group_info
            request.state.db = db
        except Exception as e:
            logger.error(f"MCP认证失败: {e}")
            return JSONResponse(
                {"error": "Authentication failed", "code": "AUTH_ERROR"}, 
                status_code=500
            )
        
        
        return await call_next(request) 