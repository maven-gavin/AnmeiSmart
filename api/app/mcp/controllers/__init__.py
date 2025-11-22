"""
MCP模块控制器导出
"""

from .mcp_config import router as mcp_config_router
from .mcp_oauth import router as mcp_oauth_router
from .mcp_server import router as mcp_server_router

__all__ = [
    "mcp_config_router",
    "mcp_oauth_router",
    "mcp_server_router",
]

