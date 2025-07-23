"""
MCP工具集合

使用装饰器模式定义的MCP工具，兼容官方库API设计。
所有工具自动注册到全局mcp_server实例。
"""

# 导入全局服务器实例
from ..server import mcp_server

# 导入所有工具模块，自动触发装饰器注册
from . import user_profile
from . import customer_analysis  
from . import conversation_data
from . import business_metrics

__all__ = [
    "mcp_server",
    "user_profile", 
    "customer_analysis",
    "conversation_data", 
    "business_metrics"
] 