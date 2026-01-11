"""MCP工具函数和辅助类"""
import hashlib
import base64
import secrets
import time
from typing import Any, Dict, Optional
from app.mcp.types import JSONRPCError, ErrorData, JSONRPCResponse


def create_mcp_error_response(request_id: Optional[str | int], code: int, message: str, data: Any = None) -> Dict[str, Any]:
    """创建MCP错误响应"""
    error = JSONRPCError(
        jsonrpc="2.0",
        id=request_id,
        error=ErrorData(code=code, message=message, data=data)
    )
    return error.model_dump(by_alias=True, exclude_none=True)


def create_mcp_success_response(request_id: Optional[str | int], result: Dict[str, Any]) -> Dict[str, Any]:
    """创建MCP成功响应"""
    response = JSONRPCResponse(
        jsonrpc="2.0",
        id=request_id,
        result=result
    )
    return response.model_dump(by_alias=True, exclude_none=True)


def base64url_sha256(data: str) -> str:
    """计算PKCE code challenge"""
    digest = hashlib.sha256(data.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')


def generate_token(prefix: str = "", length: int = 24) -> str:
    """生成安全的令牌"""
    token = secrets.token_urlsafe(length)
    return f"{prefix}_{token}" if prefix else token


def is_token_expired(created_at: int, expires_in: int) -> bool:
    """检查令牌是否已过期"""
    return int(time.time()) > (created_at + expires_in)


class MCPSession:
    """MCP会话管理"""
    def __init__(self, session_id: str, api_key: str):
        self.session_id = session_id
        self.api_key = api_key
        self.created_at = int(time.time())
        self.last_ping = self.created_at
        
    def update_ping(self):
        """更新最后一次ping时间"""
        self.last_ping = int(time.time())
        
    def is_expired(self, timeout_seconds: int = 3600) -> bool:
        """检查会话是否已过期"""
        return int(time.time()) > (self.last_ping + timeout_seconds)
