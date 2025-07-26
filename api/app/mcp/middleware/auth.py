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
        
        # 提取API Key
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(
                {"error": "Missing Authorization header", "code": "UNAUTHORIZED"}, 
                status_code=401
            )
        
        api_key = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else auth_header
        
        # 验证API Key
        db = next(get_db())
        try:
            group_info = await self.authenticator.authenticate_request(api_key, db)
            if not group_info:
                return JSONResponse(
                    {"error": "Invalid API Key", "code": "FORBIDDEN"}, 
                    status_code=403
                )
            
            # 将分组信息附加到请求状态
            request.state.mcp_group = group_info
            request.state.db = db
        except Exception as e:
            logger.error(f"MCP认证失败: {e}")
            return JSONResponse(
                {"error": "Authentication failed", "code": "AUTH_ERROR"}, 
                status_code=500
            )
        finally:
            db.close()
        
        return await call_next(request) 