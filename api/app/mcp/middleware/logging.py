"""
MCP日志记录中间件

负责记录MCP调用的详细日志和性能指标
"""

import time
from typing import Dict, Any
from sqlalchemy.orm import Session
import logging

from app.services.mcp_group_service import MCPGroupService

logger = logging.getLogger(__name__)


class MCPLoggingMiddleware:
    """MCP日志记录中间件"""
    
    def __init__(self):
        self.call_count = 0
        self.error_count = 0
    
    async def log_tool_call(
        self,
        db: Session,
        tool_name: str,
        group_id: str,
        request_data: Dict[str, Any],
        response_data: Dict[str, Any],
        success: bool,
        duration_ms: int,
        error_message: str = None
    ):
        """记录工具调用日志"""
        try:
            self.call_count += 1
            if not success:
                self.error_count += 1
            
            # 记录到数据库
            # 脱敏请求数据中的潜在敏感字段
            def _mask(obj: Dict[str, Any]) -> Dict[str, Any]:
                if not isinstance(obj, dict):
                    return obj
                masked = {}
                for k, v in obj.items():
                    if k.lower() in {"apikey", "api_key", "authorization", "token", "sessiontoken"}:
                        masked[k] = "***"
                    else:
                        masked[k] = v
                return masked

            await MCPGroupService.log_mcp_call(
                db,
                tool_name,
                group_id,
                _mask(request_data),
                _mask(response_data) if isinstance(response_data, dict) else response_data,
                success,
                duration_ms,
                error_message,
            )
            
            # 记录到应用日志
            if success:
                logger.info(f"MCP工具调用成功: {tool_name}, 耗时: {duration_ms}ms")
            else:
                logger.error(f"MCP工具调用失败: {tool_name}, 错误: {error_message}")
                
        except Exception as e:
            logger.error(f"记录MCP调用日志失败: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_calls": self.call_count,
            "error_count": self.error_count,
            "success_rate": (self.call_count - self.error_count) / max(self.call_count, 1)
        } 