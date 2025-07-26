"""
统一MCP服务器单元测试

测试基于企业级架构设计的统一MCP服务器功能
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from app.mcp.unified_server import UnifiedMCPServer, get_mcp_server


class TestUnifiedMCPServer:
    """统一MCP服务器测试类"""
    
    def test_server_initialization(self):
        """测试服务器初始化"""
        test_server = UnifiedMCPServer()
        assert test_server.app.title == "AnmeiSmart Unified MCP Server"
        assert test_server.app.version == "1.0.0"
        assert len(test_server.tool_registry.get_all_tools()) > 0
    
    def test_tool_registry(self):
        """测试工具注册功能"""
        test_server = UnifiedMCPServer()
        
        # 检查是否注册了预期的工具
        tools = test_server.tool_registry.get_all_tools()
        assert "get_user_profile" in tools
        assert "analyze_customer" in tools
        assert "get_service_info" in tools
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        server1 = get_mcp_server()
        server2 = get_mcp_server()
        assert server1 is server2 