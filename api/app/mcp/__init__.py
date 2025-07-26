"""
AnmeiSmart MCP (Model Context Protocol) Implementation

统一MCP服务器实现，支持：
- API Key认证和分组权限控制
- 动态工具路由
- 模块化架构设计
- FastAPI集成

设计符合企业级应用的安全和权限管理需求。
"""

from .unified_server import UnifiedMCPServer, get_mcp_server, create_mcp_app

__all__ = ["UnifiedMCPServer", "get_mcp_server", "create_mcp_app"] 