"""
MCP工具注册和发现模块

提供工具的自动注册、发现和管理功能
"""

from .tool_registry import MCPToolRegistry, mcp_tool, get_global_registry

__all__ = ["MCPToolRegistry", "mcp_tool", "get_global_registry"] 