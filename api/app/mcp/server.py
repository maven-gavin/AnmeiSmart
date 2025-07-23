"""
FastMCP服务器实现（兼容官方库API）

提供装饰器模式的工具定义和多传输模式支持，
API设计与官方mcp库保持一致。
"""
import asyncio
import json
import logging
import inspect
from typing import Dict, Any, Callable, Optional, List, Union
from functools import wraps
from datetime import datetime

logger = logging.getLogger(__name__)


class MCPTool:
    """MCP工具定义类"""
    
    def __init__(self, func: Callable, name: str = None, description: str = None):
        self.func = func
        self.name = name or func.__name__
        self.description = description or func.__doc__ or ""
        self.signature = inspect.signature(func)
        self.schema = self._generate_schema()
    
    def _generate_schema(self) -> Dict[str, Any]:
        """根据函数签名自动生成JSON Schema"""
        properties = {}
        required = []
        
        for param_name, param in self.signature.parameters.items():
            # 跳过self参数
            if param_name == 'self':
                continue
                
            param_schema = {"type": "string"}  # 默认类型
            
            # 根据类型注解推断Schema类型
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_schema["type"] = "integer"
                elif param.annotation == float:
                    param_schema["type"] = "number"
                elif param.annotation == bool:
                    param_schema["type"] = "boolean"
                elif param.annotation == list or str(param.annotation).startswith('typing.List'):
                    param_schema["type"] = "array"
                elif param.annotation == dict or str(param.annotation).startswith('typing.Dict'):
                    param_schema["type"] = "object"
            
            # 添加默认值
            if param.default != inspect.Parameter.empty:
                param_schema["default"] = param.default
            else:
                required.append(param_name)
            
            properties[param_name] = param_schema
        
        return {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False
        }
    
    async def execute(self, **kwargs) -> Any:
        """执行工具函数"""
        try:
            # 过滤参数，只传递函数需要的参数
            sig_params = set(self.signature.parameters.keys())
            if 'self' in sig_params:
                sig_params.remove('self')
            
            filtered_kwargs = {k: v for k, v in kwargs.items() if k in sig_params}
            
            # 执行函数
            if asyncio.iscoroutinefunction(self.func):
                result = await self.func(**filtered_kwargs)
            else:
                result = self.func(**filtered_kwargs)
            
            return result
        except Exception as e:
            logger.error(f"工具执行失败: {self.name}, error: {e}")
            raise


class FastMCP:
    """FastMCP服务器（兼容官方库API）"""
    
    def __init__(self, name: str):
        self.name = name
        self.tools: Dict[str, MCPTool] = {}
        self.server_info = {
            "name": name,
            "version": "1.0.0",
            "description": "AnmeiSmart MCP Server (Compatible Implementation)"
        }
        logger.info(f"FastMCP服务器已初始化: {name}")
    
    def tool(self, name: str = None, description: str = None):
        """
        工具装饰器（兼容官方库API）
        
        Args:
            name: 工具名称（可选，默认使用函数名）
            description: 工具描述（可选，默认使用函数文档字符串）
        """
        def decorator(func: Callable) -> Callable:
            tool_name = name or func.__name__
            tool_description = description or func.__doc__ or ""
            
            # 创建工具实例
            mcp_tool = MCPTool(func, tool_name, tool_description)
            
            # 注册工具
            self.tools[tool_name] = mcp_tool
            
            logger.info(f"MCP工具已注册: {tool_name}")
            
            # 返回原函数（保持函数可直接调用）
            return func
        
        return decorator
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """获取可用工具列表（MCP标准格式）"""
        tools_list = []
        
        for tool_name, tool in self.tools.items():
            tool_info = {
                "name": tool_name,
                "description": tool.description,
                "inputSchema": tool.schema
            }
            tools_list.append(tool_info)
        
        return tools_list
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用工具（MCP标准接口）"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool not found: {tool_name}")
        
        tool = self.tools[tool_name]
        
        try:
            result = await tool.execute(**arguments)
            
            # 转换为MCP标准响应格式
            content = []
            if isinstance(result, dict):
                content.append({
                    "type": "text",
                    "text": json.dumps(result, ensure_ascii=False, indent=2)
                })
            else:
                content.append({
                    "type": "text", 
                    "text": str(result)
                })
            
            return {
                "content": content
            }
            
        except Exception as e:
            logger.error(f"工具调用失败: {tool_name}, error: {e}")
            raise
    
    async def handle_request(self, request_data: str) -> str:
        """处理JSON-RPC 2.0请求（兼容MCP协议）"""
        try:
            request = json.loads(request_data)
            
            # 验证JSON-RPC格式
            if request.get("jsonrpc") != "2.0":
                return self._create_error_response(
                    request.get("id"), -32600, "Invalid Request"
                )
            
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            # 路由请求
            if method == "initialize":
                result = await self._handle_initialize(params)
            elif method == "tools/list":
                result = {"tools": self.get_available_tools()}
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                result = await self.call_tool(tool_name, arguments)
            else:
                return self._create_error_response(
                    request_id, -32601, f"Method not found: {method}"
                )
            
            return self._create_success_response(request_id, result)
            
        except json.JSONDecodeError:
            return self._create_error_response(None, -32700, "Parse error")
        except Exception as e:
            logger.error(f"请求处理失败: {e}")
            return self._create_error_response(
                request.get("id") if isinstance(request, dict) else None,
                -32603, f"Internal error: {str(e)}"
            )
    
    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理初始化请求"""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": self.server_info
        }
    
    def _create_success_response(self, request_id: Any, result: Dict[str, Any]) -> str:
        """创建成功响应"""
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
        return json.dumps(response, ensure_ascii=False)
    
    def _create_error_response(self, request_id: Any, code: int, message: str) -> str:
        """创建错误响应"""
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }
        return json.dumps(response, ensure_ascii=False)
    
    def run(self, transport: str = "stdio", host: str = "localhost", port: int = 8001):
        """
        启动MCP服务器（兼容官方库API）
        
        Args:
            transport: 传输模式 ("stdio", "sse", "streamable_http")
            host: 主机地址（网络模式）
            port: 端口号（网络模式）
        """
        if transport == "stdio":
            logger.info("🚀 MCP服务器启动 (stdio模式)")
            logger.info("📖 用于本地调试和测试")
            # stdio模式实现（开发调试）
            self._run_stdio_mode()
        elif transport == "sse":
            logger.info(f"🌐 MCP服务器启动 (SSE模式) - {host}:{port}")
            logger.info("🔗 用于生产环境网络通信")
            # SSE模式需要集成到FastAPI中
            self._prepare_for_sse_mode(host, port)
        elif transport == "streamable_http":
            logger.info(f"⚡ MCP服务器启动 (Streamable HTTP模式) - {host}:{port}")
            logger.info("💫 用于高并发场景")
            # Streamable HTTP模式需要集成到FastAPI中
            self._prepare_for_streamable_http_mode(host, port)
        else:
            raise ValueError(f"不支持的传输模式: {transport}")
    
    def _run_stdio_mode(self):
        """stdio模式实现（开发调试）"""
        print("MCP服务器运行在stdio模式，等待JSON-RPC请求...")
        print("输入JSON-RPC请求，按Enter发送，输入'quit'退出：")
        
        while True:
            try:
                line = input()
                if line.strip().lower() == 'quit':
                    break
                
                if line.strip():
                    response = asyncio.run(self.handle_request(line))
                    print(response)
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"错误: {e}")
        
        print("MCP服务器已停止")
    
    def _prepare_for_sse_mode(self, host: str, port: int):
        """准备SSE模式（需要FastAPI集成）"""
        logger.info(f"MCP服务器配置为SSE模式: {host}:{port}")
        logger.info("注意：SSE模式需要通过FastAPI应用启动")
    
    def _prepare_for_streamable_http_mode(self, host: str, port: int):
        """准备Streamable HTTP模式（需要FastAPI集成）"""
        logger.info(f"MCP服务器配置为Streamable HTTP模式: {host}:{port}")
        logger.info("注意：Streamable HTTP模式需要通过FastAPI应用启动")


# 创建全局MCP服务器实例
mcp_server = FastMCP("AnmeiSmart MCP Server") 