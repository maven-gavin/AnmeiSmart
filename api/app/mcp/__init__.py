"""
AnmeiSmart MCP (Model Context Protocol) Implementation

兼容官方MCP库API设计的实现，支持：
- 装饰器模式工具定义
- 多传输模式支持
- 自动类型推断和文档生成
- FastAPI集成

注意：当前使用Python 3.9兼容实现，
升级到Python 3.10+后可无缝切换到官方库。
"""

from .server import FastMCP, mcp_server

__all__ = ["FastMCP", "mcp_server"] 