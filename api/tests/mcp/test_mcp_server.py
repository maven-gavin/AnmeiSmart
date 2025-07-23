"""
MCP服务器单元测试

测试基于官方库设计的MCP服务器功能
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from app.mcp.server import FastMCP, mcp_server


class TestMCPServer:
    """MCP服务器测试类"""
    
    def test_server_initialization(self):
        """测试服务器初始化"""
        test_server = FastMCP("Test Server")
        assert test_server.name == "Test Server"
        assert test_server.server_info["name"] == "Test Server"
        assert len(test_server.tools) == 0
    
    def test_tool_registration(self):
        """测试工具注册功能"""
        test_server = FastMCP("Test Server")
        
        @test_server.tool()
        def test_function(param1: str, param2: int = 10) -> str:
            """测试函数"""
            return f"param1={param1}, param2={param2}"
        
        assert len(test_server.tools) == 1
        assert "test_function" in test_server.tools
        
        tool = test_server.tools["test_function"]
        assert tool.name == "test_function"
        assert tool.description == "测试函数"
    
    def test_tool_schema_generation(self):
        """测试工具Schema自动生成"""
        test_server = FastMCP("Test Server")
        
        @test_server.tool()
        def test_typed_function(user_id: str, count: int = 5, enabled: bool = True) -> dict:
            """带类型注解的测试函数"""
            return {"user_id": user_id, "count": count, "enabled": enabled}
        
        tools = test_server.get_available_tools()
        assert len(tools) == 1
        
        tool_schema = tools[0]["inputSchema"]
        properties = tool_schema["properties"]
        
        # 验证类型推断
        assert properties["user_id"]["type"] == "string"
        assert properties["count"]["type"] == "integer"
        assert properties["enabled"]["type"] == "boolean"
        
        # 验证必需参数
        assert "user_id" in tool_schema["required"]
        assert "count" not in tool_schema["required"]  # 有默认值
        assert "enabled" not in tool_schema["required"]  # 有默认值
    
    @pytest.mark.asyncio
    async def test_tool_execution(self):
        """测试工具执行"""
        test_server = FastMCP("Test Server")
        
        @test_server.tool()
        async def async_test_function(name: str) -> dict:
            """异步测试函数"""
            return {"greeting": f"Hello, {name}!"}
        
        result = await test_server.call_tool("async_test_function", {"name": "World"})
        
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        
        # 解析返回的JSON内容
        import json
        response_data = json.loads(result["content"][0]["text"])
        assert response_data["greeting"] == "Hello, World!"
    
    @pytest.mark.asyncio
    async def test_jsonrpc_handling(self):
        """测试JSON-RPC请求处理"""
        test_server = FastMCP("Test Server")
        
        @test_server.tool()
        def simple_tool(message: str) -> str:
            """简单工具"""
            return f"Received: {message}"
        
        # 测试tools/list请求
        list_request = '{"jsonrpc": "2.0", "id": "1", "method": "tools/list", "params": {}}'
        response = await test_server.handle_request(list_request)
        
        import json
        response_data = json.loads(response)
        
        assert response_data["jsonrpc"] == "2.0"
        assert response_data["id"] == "1"
        assert "result" in response_data
        assert len(response_data["result"]["tools"]) == 1
        assert response_data["result"]["tools"][0]["name"] == "simple_tool"
        
        # 测试tools/call请求
        call_request = '''{"jsonrpc": "2.0", "id": "2", "method": "tools/call", 
                          "params": {"name": "simple_tool", "arguments": {"message": "test"}}}'''
        response = await test_server.handle_request(call_request)
        
        response_data = json.loads(response)
        assert response_data["jsonrpc"] == "2.0"
        assert response_data["id"] == "2"
        assert "result" in response_data
    
    def test_global_server_instance(self):
        """测试全局服务器实例"""
        assert mcp_server.name == "AnmeiSmart MCP Server"
        assert isinstance(mcp_server, FastMCP)


class TestMCPToolsIntegration:
    """MCP工具集成测试"""
    
    def test_tools_registration(self):
        """测试工具模块的自动注册"""
        # 导入工具模块会自动注册工具到全局服务器
        import app.mcp.tools  # noqa
        
        # 验证工具已注册
        expected_tools = ["get_user_profile", "analyze_customer", "get_conversation_data", "get_business_metrics"]
        
        for tool_name in expected_tools:
            assert tool_name in mcp_server.tools, f"Tool {tool_name} not registered"
    
    def test_tool_schemas(self):
        """测试已注册工具的Schema"""
        import app.mcp.tools  # noqa
        
        tools = mcp_server.get_available_tools()
        assert len(tools) >= 4
        
        # 验证每个工具都有正确的Schema
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            
            schema = tool["inputSchema"]
            assert "type" in schema
            assert "properties" in schema
            assert "required" in schema
    
    @pytest.mark.asyncio
    async def test_user_profile_tool(self):
        """测试用户信息工具"""
        import app.mcp.tools  # noqa
        
        # 使用不存在的用户ID测试错误处理
        result = await mcp_server.call_tool("get_user_profile", {"user_id": "nonexistent", "include_details": False})
        
        assert "content" in result
        content_text = result["content"][0]["text"]
        
        import json
        response_data = json.loads(content_text)
        assert "error" in response_data
        assert response_data["error_code"] == "USER_NOT_FOUND" 