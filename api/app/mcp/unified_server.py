"""
统一MCP服务器 - 模块化架构

核心框架，负责：
- 服务器启动和路由管理
- 请求分发和响应处理
- 组件协调和生命周期管理

工具实现完全分离到独立模块中，遵循单一职责原则
"""

from fastapi import FastAPI, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from sqlalchemy.orm import Session
import logging
import json

from app.mcp.registry import get_global_registry
from app.mcp.middleware import MCPAuthenticator, MCPMiddleware, MCPLoggingMiddleware
from app.services.mcp_group_service import MCPGroupService
from app.db.base import get_db
from app.core.config import get_settings
from app.mcp.session_manager import (
    issue_session_token,
    validate_session_token,
    save_auth_code_mapping,
    consume_auth_code,
)

logger = logging.getLogger(__name__)


class JSONRPCHandler:
    """JSON-RPC 2.0 处理器，专门为 Dify 兼容性设计"""
    
    def __init__(self, tool_registry, authenticator: MCPAuthenticator):
        self.tool_registry = tool_registry
        self.authenticator = authenticator
        self.settings = get_settings()
    
    async def handle_request(self, request_data: dict, db: Session, headers: dict = None) -> dict:
        """处理 JSON-RPC 2.0 请求"""
        try:
            # 记录收到的请求
            logger.info(f"收到 JSON-RPC 请求: {request_data}")
            
            # 验证 JSON-RPC 格式
            if not self._validate_jsonrpc_request(request_data):
                logger.warning(f"无效的 JSON-RPC 请求格式: {request_data}")
                return self._error_response(
                    request_data.get("id"), -32600, "Invalid Request"
                )
            
            method = request_data.get("method")
            params = request_data.get("params", {})
            request_id = request_data.get("id")
            
            logger.info(f"处理方法: {method}, 请求ID: {request_id}, 参数: {params}")
            
            # 路由到具体的方法处理
            if method == "initialize":
                result = await self._handle_initialize(request_id, params, db, headers)
                logger.info(f"initialize 处理结果: {result}")
                return result
            elif method == "initialized" or method == "notifications/initialized":
                result = await self._handle_initialized(request_id, params)
                logger.info(f"initialized/notifications/initialized 处理结果: {result}")
                return result
            elif method == "tools/list":
                return await self._handle_tools_list(request_id, params, db)
            elif method == "tools/call":
                return await self._handle_tools_call(request_id, params, db)
            elif method == "ping":
                return self._handle_ping(request_id)
            else:
                logger.warning(f"未知方法: {method}")
                return self._error_response(
                    request_id, -32601, f"Method not found: {method}"
                )
                
        except Exception as e:
            logger.error(f"JSON-RPC 处理失败: {e}", exc_info=True)
            return self._error_response(
                request_data.get("id"), -32603, "Internal error"
            )
    
    def _validate_jsonrpc_request(self, request_data: dict) -> bool:
        """验证 JSON-RPC 2.0 请求格式"""
        if not isinstance(request_data, dict):
            logger.warning(f"请求数据不是字典: {type(request_data)}")
            return False
            
        if request_data.get("jsonrpc") != "2.0":
            logger.warning(f"错误的 JSON-RPC 版本: {request_data.get('jsonrpc')}")
            return False
            
        if "method" not in request_data:
            logger.warning(f"缺少 method 字段: {request_data}")
            return False
            
        method = request_data.get("method")
        if not isinstance(method, str) or not method.strip():
            logger.warning(f"method 字段无效: {method}")
            return False
            
        # 验证 ID 字段（如果存在）
        request_id = request_data.get("id")
        if "id" in request_data and request_id is not None:
            if not isinstance(request_id, (str, int)):
                logger.warning(f"ID 类型无效: {type(request_id)}, 值: {request_id}")
                return False
        
        logger.debug(f"JSON-RPC 请求验证通过: method={method}, id={request_id}")
        return True
    
    async def _handle_initialize(self, request_id: Union[str, int], params: dict, db: Session, headers: dict = None) -> dict:
        """处理初始化请求 - 支持 Dify OAuth 流程"""
        try:
            # 首先检查 Authorization 头中的 access_token（Dify 标准做法）
            access_token = None
            if headers:
                auth_header = headers.get("authorization") or headers.get("Authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    access_token = auth_header.replace("Bearer ", "").strip()
            
            # 提取 API Key（兼容性支持）
            api_key = params.get("apiKey")
            client_info = params.get("clientInfo", {})
            
            # 优先验证 access_token（sessionToken）
            group_info = None
            if access_token:
                from app.mcp.session_manager import validate_session_token
                session_data = await validate_session_token(access_token)
                if session_data:
                    group_info = {
                        "id": session_data.get("group_id"),
                        "name": session_data.get("group_name"),
                        "tools": session_data.get("allowed_tools", [])
                    }
            
            # 如果没有有效的 access_token，尝试 API Key
            if not group_info and api_key:
                group_info = await self.authenticator.authenticate_request(api_key, db)
            
            # 如果已通过 access_token 验证成功，直接返回成功响应
            if group_info:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": self.settings.MCP_PROTOCOL_VERSION,
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": self.settings.MCP_SERVER_NAME,
                            "version": self.settings.VERSION
                        },
                        "status": "success"
                    }
                }
            
            # 如果没有 API Key 和 access_token，返回包含授权 URL 的标准响应
            if not api_key and not access_token:
                # 生成授权 URL，让 Dify 弹出授权窗口
                state = f"init_{int(time.time())}"
                authorization_url = (
                    f"{self.settings.MCP_AUTH_BASE_URL}?client_id={client_info.get('name', 'dify')}"
                    f"&redirect_uri={self.settings.MCP_OAUTH_REDIRECT_URI}"
                    f"&state={state}&response_type=code"
                )
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": self.settings.MCP_PROTOCOL_VERSION,
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": self.settings.MCP_SERVER_NAME,
                            "version": self.settings.VERSION
                        },
                        "authorization_url": authorization_url,
                        "status": "authorization_required"
                    }
                }
            
            # 如果有 API Key 但无效，返回重新授权URL
            if api_key:
                # API Key 无效时返回包含重新授权 URL 的标准响应
                state = f"reauth_{int(time.time())}"
                authorization_url = (
                    f"{self.settings.MCP_AUTH_BASE_URL}?client_id={client_info.get('name', 'dify')}"
                    f"&redirect_uri={self.settings.MCP_OAUTH_REDIRECT_URI}"
                    f"&state={state}&response_type=code&error=invalid_api_key"
                )
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": self.settings.MCP_PROTOCOL_VERSION,
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": self.settings.MCP_SERVER_NAME,
                            "version": self.settings.VERSION
                        },
                        "authorization_url": authorization_url,
                        "status": "reauthorization_required",
                        "error": "Invalid API Key"
                    }
                }
            else:
                # access_token 无效，返回需要重新授权
                state = f"reauth_{int(time.time())}"
                authorization_url = (
                    f"{self.settings.MCP_AUTH_BASE_URL}?client_id={client_info.get('name', 'dify')}"
                    f"&redirect_uri={self.settings.MCP_OAUTH_REDIRECT_URI}"
                    f"&state={state}&response_type=code&error=invalid_token"
                )
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": self.settings.MCP_PROTOCOL_VERSION,
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": self.settings.MCP_SERVER_NAME,
                            "version": self.settings.VERSION
                        },
                        "authorization_url": authorization_url,
                        "status": "reauthorization_required",
                        "error": "Invalid or expired access token"
                    }
                }
            
        except Exception as e:
            logger.error(f"Initialize 处理失败: {e}")
            return self._error_response(
                request_id, -32603, "Initialization failed"
            )
    
    async def _handle_initialized(self, request_id: Union[str, int, None], params: dict) -> dict:
        """处理初始化完成通知"""
        logger.info(f"处理 initialized 通知，request_id: {request_id}, params: {params}")
        
        # initialized 通常是一个通知消息（没有响应）
        # 但我们记录这个事件并返回空响应
        if request_id is None:
            # 这是一个标准的通知，不需要响应
            logger.info("收到 initialized 通知（无需响应）")
            return None
        
        # 如果有 request_id，返回确认响应
        logger.info(f"收到带ID的 initialized 请求，返回确认响应")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"status": "initialized"}
        }
    
    async def _handle_tools_list(self, request_id: Union[str, int], params: dict, db: Session) -> dict:
        """处理工具列表请求"""
        try:
            # 读取会话令牌（可选）
            session_token = params.get("sessionToken")
            session = await validate_session_token(session_token) if session_token else None
            
            # 确定可用工具
            if session:
                # 已认证：返回该分组的工具
                available_tools = await MCPGroupService.get_group_tools(db, session["group_id"])
            else:
                # 未认证：返回所有注册的工具（用于预览）
                available_tools = self.tool_registry.get_all_tools()
            
            # 构建工具列表响应
            tools = []
            for tool_name in available_tools:
                if self.tool_registry.is_tool_registered(tool_name):
                    metadata = self.tool_registry.get_tool_metadata(tool_name)
                    # 构建 JSON Schema（从工具签名推导）
                    input_schema = self.tool_registry.build_input_schema(tool_name)
                    tools.append({
                        "name": tool_name,
                        "description": metadata.description,
                        "inputSchema": input_schema
                    })
            
            logger.info(f"tools/list 返回 {len(tools)} 个工具 (认证状态: {'已认证' if session else '未认证'})")
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": tools
                }
            }
            
        except Exception as e:
            logger.error(f"Tools list 处理失败: {e}")
            return self._error_response(
                request_id, -32603, "Failed to retrieve tools"
            )
    
    async def _handle_tools_call(self, request_id: Union[str, int], params: dict, db: Session) -> dict:
        """处理工具调用请求"""
        try:
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            session_token = params.get("sessionToken")
            
            if not tool_name:
                return self._error_response(
                    request_id, -32602, "Tool name is required"
                )
            
            # 验证会话
            session = await validate_session_token(session_token)
            if not session:
                return self._error_response(request_id, -32602, "Authentication required")
            
            # 检查工具是否存在
            if not self.tool_registry.is_tool_registered(tool_name):
                return self._error_response(
                    request_id, -32602, f"Tool '{tool_name}' not found"
                )
            
            # 检查权限
            has_permission = await self.authenticator.check_tool_permission(
                {"id": session["group_id"]}, tool_name, db
            )
            if not has_permission:
                return self._error_response(
                    request_id, -32602, f"Permission denied for tool '{tool_name}'"
                )
            
            # 执行工具
            tool_func = self.tool_registry.get_tool(tool_name)
            result = await tool_func(**arguments)

            # 返回工具执行结果（优先提供 JSON 通道，同时附加文本摘要）
            content_items = []
            if isinstance(result, (dict, list)):
                content_items.append({
                    "type": "json",
                    "json": result
                })
                content_items.append({
                    "type": "text",
                    "text": json.dumps(result, ensure_ascii=False)
                })
            else:
                content_items.append({
                    "type": "text",
                    "text": str(result)
                })

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": content_items
                }
            }
            
        except Exception as e:
            logger.error(f"Tool call 处理失败: {e}")
            return self._error_response(
                request_id, -32603, f"Tool execution failed: {str(e)}"
            )
    
    def _handle_ping(self, request_id: Union[str, int]) -> dict:
        """处理 ping 健康检查"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "server": "AnmeiSmart MCP Server"
            }
        }
    
    def _error_response(self, request_id: Union[str, int, None], code: int, message: str, data: dict = None) -> dict:
        """构建错误响应"""
        error = {
            "code": code,
            "message": message
        }
        if data:
            error["data"] = data
        
        # 确保 request_id 不为 None，如果为 None 则使用字符串 "null"
        safe_request_id = request_id if request_id is not None else "unknown"
            
        response = {
            "jsonrpc": "2.0",
            "id": safe_request_id,
            "error": error
        }
        
        logger.debug(f"构建错误响应: {response}")
        return response


class MCPRequestRouter:
    """MCP请求路由器 - 负责请求的路由和分发"""
    
    def __init__(self, authenticator: MCPAuthenticator, logging_middleware: MCPLoggingMiddleware):
        self.tool_registry = get_global_registry()
        self.authenticator = authenticator
        self.logging_middleware = logging_middleware
    
    async def route_tool_call(
        self, 
        tool_name: str, 
        params: dict, 
        group_info: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """路由工具调用"""
        start_time = time.time()
        
        try:
            # 检查工具是否存在
            if not self.tool_registry.is_tool_registered(tool_name):
                return {
                    "error": f"工具 '{tool_name}' 未注册",
                    "code": "TOOL_NOT_FOUND"
                }
            
            # 检查权限
            has_permission = await self.authenticator.check_tool_permission(
                group_info, tool_name, db
            )
            if not has_permission:
                return {
                    "error": f"工具 '{tool_name}' 不在分组内或已禁用",
                    "code": "PERMISSION_DENIED"
                }
            
            # 执行工具
            tool_func = self.tool_registry.get_tool(tool_name)
            result = await tool_func(**params)
            
            # 记录成功调用
            duration_ms = int((time.time() - start_time) * 1000)
            await self.logging_middleware.log_tool_call(
                db, tool_name, group_info["id"], params, result, True, duration_ms
            )
            
            return {"success": True, "data": result}
            
        except Exception as e:
            # 记录失败调用
            duration_ms = int((time.time() - start_time) * 1000)
            error_result = {"error": str(e), "code": "EXECUTION_ERROR"}
            
            await self.logging_middleware.log_tool_call(
                db, tool_name, group_info["id"], params, error_result, False, duration_ms, str(e)
            )
            
            return error_result


class UnifiedMCPServer:
    """统一MCP Server - 模块化架构，分离关注点"""
    
    def __init__(self):
        self.app = FastAPI(
            title="AnmeiSmart Unified MCP Server",
            version="1.0.0",
            description="统一MCP服务器支持多分组权限控制和模块化工具管理"
        )
        
        # 初始化组件
        self.tool_registry = get_global_registry()
        self.authenticator = MCPAuthenticator()
        self.logging_middleware = MCPLoggingMiddleware()
        self.router = MCPRequestRouter(self.authenticator, self.logging_middleware)
        self.middleware = MCPMiddleware(self.authenticator)
        
        # 初始化 JSON-RPC 处理器（为 Dify 兼容性）
        self.jsonrpc_handler = JSONRPCHandler(self.tool_registry, self.authenticator)
        
        # 服务器启动时间
        self.server_start_time = time.time()
        
        # 初始化服务器
        self._setup_middleware()
        self._setup_routes()
        self._discover_and_register_tools()

    def _setup_middleware(self):
        """设置中间件"""
        # CORS中间件
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # MCP认证中间件
        @self.app.middleware("http")
        async def mcp_auth_middleware(request: Request, call_next):
            return await self.middleware.process_request(request, call_next)

    def _setup_routes(self):
        """设置MCP API路由"""
        
        @self.app.get("/mcp/tools")
        async def list_available_tools(request: Request):
            """返回当前API Key可用的工具列表"""
            group = getattr(request.state, "mcp_group", None)
            db = getattr(request.state, "db", None)
            
            if not group or not db:
                return {"tools": []}
            
            # 从数据库获取分组内的工具列表
            available_tools = await MCPGroupService.get_group_tools(db, group["id"])
            
            # 返回工具信息，包含分类信息
            tools_with_metadata = []
            for tool_name in available_tools:
                if self.tool_registry.is_tool_registered(tool_name):
                    metadata = self.tool_registry.get_tool_metadata(tool_name)
                    tools_with_metadata.append({
                        "name": tool_name,
                        "description": metadata.description,
                        "category": metadata.category,
                        "group": group["name"],
                        "module": metadata.module
                    })
            
            return {
                "tools": tools_with_metadata,
                "total_tools": len(tools_with_metadata),
                "categories": list(set(tool["category"] for tool in tools_with_metadata))
            }
        
        @self.app.post("/mcp/call/{tool_name}")
        async def call_tool(tool_name: str, params: dict, request: Request):
            """调用MCP工具"""
            group = getattr(request.state, "mcp_group", None)
            db = getattr(request.state, "db", None)
            
            if not group or not db:
                return JSONResponse(
                    {"error": "Unauthorized", "code": "UNAUTHORIZED"}, 
                    status_code=403
                )
            
            result = await self.router.route_tool_call(tool_name, params, group, db)
            
            if "error" in result:
                status_code = 404 if result.get("code") == "TOOL_NOT_FOUND" else 500
                return JSONResponse(result, status_code=status_code)
            
            return result

        @self.app.get("/mcp/server/info")
        async def server_info():
            """获取MCP服务器信息"""
            return {
                "name": "AnmeiSmart Unified MCP Server",
                "version": "1.0.0",
                "description": "统一MCP服务器支持多分组权限控制和模块化工具管理",
                "uptime_seconds": int(time.time() - self.server_start_time),
                "registered_tools": len(self.tool_registry.get_all_tools()),
                "tool_categories": self.tool_registry.get_all_categories(),
                "transport": "http",
                "architecture": "modular"
            }

        @self.app.get("/mcp/tools/info")
        async def tools_info():
            """获取所有工具的详细信息（管理员接口）"""
            return {
                "tools": self.tool_registry.get_tools_info(),
                "statistics": self.logging_middleware.get_stats()
            }

        @self.app.get("/mcp/admin/tools/all")
        async def get_all_tools_for_admin():
            """获取所有注册工具信息（管理员内部接口，无需认证）"""
            all_tools = []
            for tool_name in self.tool_registry.get_all_tools():
                metadata = self.tool_registry.get_tool_metadata(tool_name)
                all_tools.append({
                    "name": tool_name,
                    "description": metadata.description,
                    "category": metadata.category,
                    "module": metadata.module
                })
            
            return {
                "tools": all_tools,
                "total_tools": len(all_tools),
                "categories": self.tool_registry.get_all_categories()
            }



        # 根路径处理，避免重定向问题
        @self.app.get("/")
        @self.app.post("/")
        async def mcp_root():
            """MCP根路径，避免重定向问题"""
            return {
                "server": "AnmeiSmart Unified MCP Server",
                "version": "1.0.0",
                "status": "online",
                "endpoints": {
                    "tools": "/mcp/tools",
                    "call": "/mcp/call/{tool_name}",
                    "info": "/mcp/server/info",
                    "oauth": {
                        "register": "/mcp/register",
                        "authorize": "/mcp/oauth/authorize",
                        "token": "/mcp/oauth/token"
                    }
                }
            }

        # OAuth相关端点（支持Dify集成）
        @self.app.post("/register")
        async def oauth_register():
            """OAuth客户端注册端点（模拟，返回静态配置）"""
            return {
                "client_id": "anmeismart_mcp_client",
                "client_secret": "anmeismart_mcp_secret",
                "authorization_endpoint": f"http://localhost:8000/mcp/oauth/authorize",
                "token_endpoint": f"http://localhost:8000/mcp/oauth/token",
                "scope": "mcp:tools"
            }

        @self.app.get("/.well-known/oauth-authorization-server")
        async def oauth_discovery():
            """OAuth授权服务器发现端点"""
            return {
                "issuer": "http://localhost:8000/mcp",
                "authorization_endpoint": "http://localhost:8000/mcp/oauth/authorize",
                "token_endpoint": "http://localhost:8000/mcp/oauth/token",
                "registration_endpoint": "http://localhost:8000/mcp/register",
                "scopes_supported": ["mcp:tools"],
                "response_types_supported": ["code"],
                "grant_types_supported": ["authorization_code"],
                "token_endpoint_auth_methods_supported": ["client_secret_basic"]
            }

        @self.app.get("/oauth/authorize")
        async def oauth_authorize_form(
            client_id: str, 
            redirect_uri: str, 
            scope: str = "mcp:tools",
            response_type: str = "code",
            state: str = None,
            error: str = None
        ):
            """OAuth授权页面 - Dify 兼容的 API 密钥输入界面"""
            
            # 判断是否为重新授权（API Key 无效）
            is_reauth = error == "invalid_api_key"
            title = "重新授权 - API密钥无效" if is_reauth else "AnmeiSmart MCP 服务授权"
            
            error_message = ""
            if is_reauth:
                error_message = """
                <div class="error-message">
                    <p><strong>⚠️ 认证失败</strong></p>
                    <p>您之前提供的API密钥无效或已过期，请重新输入正确的API密钥。</p>
                </div>
                """
            
            # 返回优化的HTML表单
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{title}</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{ 
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                        max-width: 500px; 
                        margin: 50px auto; 
                        padding: 20px;
                        background: #f8fafc;
                        line-height: 1.6;
                    }}
                    .form-container {{ 
                        background: white; 
                        padding: 40px; 
                        border-radius: 12px; 
                        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                        border: 1px solid #e2e8f0;
                    }}
                    .header {{
                        text-align: center;
                        margin-bottom: 30px;
                    }}
                    .logo {{
                        width: 48px;
                        height: 48px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        border-radius: 12px;
                        margin: 0 auto 15px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: white;
                        font-size: 20px;
                        font-weight: bold;
                    }}
                    h2 {{ 
                        margin: 0; 
                        color: #1a202c; 
                        font-size: 24px; 
                        font-weight: 600;
                    }}
                    .subtitle {{
                        color: #64748b;
                        font-size: 14px;
                        margin-top: 5px;
                    }}
                    .form-group {{ margin-bottom: 24px; }}
                    label {{ 
                        display: block; 
                        margin-bottom: 8px; 
                        font-weight: 500; 
                        color: #374151;
                        font-size: 14px;
                    }}
                    input[type="password"] {{ 
                        width: 100%; 
                        padding: 12px 16px; 
                        border: 2px solid #e2e8f0; 
                        border-radius: 8px; 
                        font-size: 16px;
                        transition: border-color 0.2s;
                        box-sizing: border-box;
                    }}
                    input[type="password"]:focus {{ 
                        outline: none; 
                        border-color: #667eea; 
                        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
                    }}
                    .button-group {{
                        display: flex;
                        gap: 12px;
                        margin-top: 32px;
                    }}
                    .btn-primary {{ 
                        flex: 1;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        color: white; 
                        padding: 12px 24px; 
                        border: none; 
                        border-radius: 8px; 
                        cursor: pointer; 
                        font-size: 16px;
                        font-weight: 500;
                        transition: transform 0.2s, box-shadow 0.2s;
                    }}
                    .btn-primary:hover {{ 
                        transform: translateY(-1px);
                        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
                    }}
                    .btn-secondary {{
                        flex: 1;
                        background: #f8fafc;
                        color: #64748b;
                        padding: 12px 24px;
                        border: 2px solid #e2e8f0;
                        border-radius: 8px;
                        cursor: pointer;
                        font-size: 16px;
                        font-weight: 500;
                        transition: all 0.2s;
                    }}
                    .btn-secondary:hover {{
                        background: #f1f5f9;
                        border-color: #cbd5e1;
                    }}
                    .info {{ 
                        background: #eff6ff; 
                        border: 1px solid #bfdbfe;
                        padding: 16px; 
                        border-radius: 8px; 
                        margin-bottom: 24px;
                        font-size: 14px;
                    }}
                    .error-message {{
                        background: #fef2f2;
                        border: 1px solid #fecaca;
                        color: #dc2626;
                        padding: 16px;
                        border-radius: 8px;
                        margin-bottom: 24px;
                        font-size: 14px;
                    }}
                    .help-text {{ 
                        color: #64748b; 
                        font-size: 12px; 
                        margin-top: 24px; 
                        text-align: center;
                        line-height: 1.5;
                    }}
                    .help-text a {{
                        color: #667eea;
                        text-decoration: none;
                    }}
                    .help-text a:hover {{
                        text-decoration: underline;
                    }}
                </style>
            </head>
            <body>
                <div class="form-container">
                    <div class="header">
                        <div class="logo">AS</div>
                        <h2>{title}</h2>
                        <div class="subtitle">连接到 {client_id}</div>
                    </div>
                    
                    {error_message}
                    
                    <div class="info">
                        <p><strong>📋 授权请求</strong></p>
                        <p>Dify 请求访问您的 AnmeiSmart MCP 工具集。请输入有效的 API 密钥以完成授权。</p>
                    </div>
                    
                    <form method="post" action="/oauth/authorize/submit" id="authForm">
                        <input type="hidden" name="client_id" value="{client_id}">
                        <input type="hidden" name="redirect_uri" value="{redirect_uri}">
                        <input type="hidden" name="scope" value="{scope}">
                        <input type="hidden" name="response_type" value="{response_type}">
                        <input type="hidden" name="state" value="{state or ''}">
                        
                        <div class="form-group">
                            <label for="api_key">🔑 API 密钥</label>
                            <input type="password" 
                                   id="api_key" 
                                   name="api_key" 
                                   placeholder="请输入您的 AnmeiSmart MCP API 密钥"
                                   required
                                   autocomplete="off">
                        </div>
                        
                        <div class="button-group">
                            <button type="button" class="btn-secondary" onclick="window.close()">
                                取消
                            </button>
                            <button type="submit" class="btn-primary">
                                🚀 授权访问
                            </button>
                        </div>
                    </form>
                    
                    <div class="help-text">
                        💡 您可以在 <a href="http://localhost:3000/settings" target="_blank">AnmeiSmart 管理后台</a> 的 MCP 配置面板中创建和管理 API 密钥。<br>
                        首次使用？创建新的 MCP 分组后，复制生成的 API 密钥即可。
                    </div>
                </div>
                
                <script>
                    // 自动聚焦到API密钥输入框
                    document.getElementById('api_key').focus();
                    
                    // 表单提交时显示加载状态
                    document.getElementById('authForm').addEventListener('submit', function(e) {{
                        const submitBtn = e.target.querySelector('.btn-primary');
                        submitBtn.innerHTML = '🔄 验证中...';
                        submitBtn.disabled = true;
                    }});
                    
                    // Enter键快捷提交
                    document.getElementById('api_key').addEventListener('keypress', function(e) {{
                        if (e.key === 'Enter') {{
                            document.getElementById('authForm').submit();
                        }}
                    }});
                </script>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)

        @self.app.post("/oauth/authorize/submit")
        async def oauth_authorize_submit(request: Request):
            """处理授权表单提交 - Dify 兼容版本"""
            form_data = await request.form()
            api_key = form_data.get("api_key")
            client_id = form_data.get("client_id")
            redirect_uri = form_data.get("redirect_uri")
            scope = form_data.get("scope")
            state = form_data.get("state")
            
            # 验证API密钥
            db = next(get_db())
            try:
                from app.services.mcp_group_service import MCPGroupService
                group_info = await MCPGroupService.validate_api_key(db, api_key)
                
                if not group_info:
                    # API密钥无效，显示美化的错误页面并提供重试选项
                    error_html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>授权失败</title>
                        <meta charset="utf-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <style>
                            body {{ 
                                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                                max-width: 500px; 
                                margin: 50px auto; 
                                padding: 20px;
                                background: #f8fafc;
                                line-height: 1.6;
                                text-align: center;
                            }}
                            .error-container {{ 
                                background: white; 
                                padding: 40px; 
                                border-radius: 12px; 
                                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                                border: 1px solid #fee2e2;
                            }}
                            .error-icon {{
                                font-size: 48px;
                                margin-bottom: 20px;
                            }}
                            h2 {{ 
                                color: #dc2626; 
                                margin-bottom: 16px;
                                font-size: 24px;
                            }}
                            p {{ 
                                color: #64748b; 
                                margin-bottom: 24px;
                            }}
                            .btn-retry {{ 
                                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                color: white; 
                                padding: 12px 24px; 
                                border: none; 
                                border-radius: 8px; 
                                cursor: pointer; 
                                font-size: 16px;
                                font-weight: 500;
                                text-decoration: none;
                                display: inline-block;
                                margin-right: 12px;
                            }}
                            .btn-close {{
                                background: #f8fafc;
                                color: #64748b;
                                padding: 12px 24px;
                                border: 2px solid #e2e8f0;
                                border-radius: 8px;
                                cursor: pointer;
                                font-size: 16px;
                                font-weight: 500;
                                text-decoration: none;
                                display: inline-block;
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="error-container">
                            <div class="error-icon">🔐</div>
                            <h2>API 密钥验证失败</h2>
                            <p>您输入的 API 密钥无效或已过期。请检查密钥是否正确，并确保对应的 MCP 分组已启用。</p>
                            <a href="javascript:history.back()" class="btn-retry">🔄 重新输入</a>
                            <a href="javascript:window.close()" class="btn-close">关闭窗口</a>
                            <p style="margin-top: 24px; font-size: 12px; color: #9ca3af;">
                                💡 提示：您可以在 <a href="http://localhost:3000/settings" target="_blank" style="color: #667eea;">AnmeiSmart 管理后台</a> 中检查您的 API 密钥状态
                            </p>
                        </div>
                    </body>
                    </html>
                    """
                    return HTMLResponse(content=error_html, status_code=400)
                
                # 生成授权码并存储映射（Redis）
                auth_code = f"auth_code_{int(time.time())}_{group_info['id']}"
                await save_auth_code_mapping(
                    auth_code,
                    {
                        "api_key": api_key,
                        "group_info": group_info,
                        "client_id": client_id,
                        "created_at": time.time(),
                    },
                    ttl_seconds=600,
                )
                
                # 构建重定向URL（符合 OAuth 2.0 标准）
                redirect_url = f"{redirect_uri}?code={auth_code}"
                if state:
                    redirect_url += f"&state={state}"
                
                logger.info(f"OAuth 授权成功: 分组={group_info['name']}, 客户端={client_id}, 重定向到={redirect_uri}")
                
                return RedirectResponse(url=redirect_url)
                
            except Exception as e:
                logger.error(f"OAuth授权验证失败: {e}")
                error_html = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>系统错误</title>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                        body { 
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                            max-width: 500px; 
                            margin: 50px auto; 
                            padding: 20px;
                            background: #f8fafc;
                            text-align: center;
                        }
                        .error-container { 
                            background: white; 
                            padding: 40px; 
                            border-radius: 12px; 
                            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                        }
                    </style>
                </head>
                <body>
                    <div class="error-container">
                        <h2 style="color: #dc2626;">⚠️ 系统错误</h2>
                        <p>授权过程中发生内部错误，请稍后重试。</p>
                        <button onclick="history.back()" style="background: #667eea; color: white; padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer;">返回重试</button>
                        <button onclick="window.close()" style="background: #f8fafc; color: #64748b; padding: 12px 24px; border: 2px solid #e2e8f0; border-radius: 8px; cursor: pointer; margin-left: 12px;">关闭</button>
                    </div>
                </body>
                </html>
                """
                return HTMLResponse(content=error_html, status_code=500)
            finally:
                db.close()

        @self.app.post("/oauth/token")
        async def oauth_token(request: Request):
            """OAuth令牌端点 - 支持表单和JSON请求"""
            try:
                # 尝试解析JSON请求体
                if request.headers.get("content-type", "").startswith("application/json"):
                    data = await request.json()
                else:
                    # 解析表单数据
                    form_data = await request.form()
                    data = dict(form_data)
                
                grant_type = data.get("grant_type")
                code = data.get("code")
                client_id = data.get("client_id")
                client_secret = data.get("client_secret")
                
                logger.info(f"OAuth token 请求: grant_type={grant_type}, code={code}, client_id={client_id}")
                
                # 验证必需参数
                if not grant_type or grant_type != "authorization_code":
                    return JSONResponse(
                        {"error": "unsupported_grant_type", "error_description": "Only authorization_code grant type is supported"},
                        status_code=400
                    )
                
                if not code:
                    return JSONResponse(
                        {"error": "invalid_request", "error_description": "Missing authorization code"},
                        status_code=400
                    )
                
                # 验证授权码并获取对应的API密钥
                auth_data = await consume_auth_code(code)
                if not auth_data:
                    logger.warning(f"无效的授权码: {code}")
                    return JSONResponse(
                        {"error": "invalid_grant", "error_description": "Invalid or expired authorization code"},
                        status_code=400
                    )
                
                # 获取API密钥和分组信息
                api_key = auth_data["api_key"]
                group_info = auth_data["group_info"]
                
                # 使用后删除授权码（一次性使用）- 已在 consume_auth_code 中处理，无需额外删除
                
                # 颁发会话令牌（Dify 后续可以直接使用）
                try:
                    from app.db.base import get_db as _get_db
                    _db = next(_get_db())
                    allowed_tools = await MCPGroupService.get_group_tools(_db, group_info["id"]) if _db else []
                except Exception:
                    allowed_tools = []
                session_token = await issue_session_token(group_info, client_id or "dify", allowed_tools)
                token_response = {
                    "access_token": session_token,
                    "token_type": "Bearer",
                    "expires_in": 3600,
                    "scope": "mcp:tools",
                    "group_id": group_info["id"],
                    "group_name": group_info["name"]
                }
                
                logger.info(f"OAuth token 颁发成功: 分组={group_info['name']}, 客户端={client_id}")
                
                return JSONResponse(content=token_response)
                
            except Exception as e:
                logger.error(f"OAuth token 处理失败: {e}")
                return JSONResponse(
                    {"error": "server_error", "error_description": "Internal server error"},
                    status_code=500
                )



        @self.app.get("/health")
        async def health_check():
            """健康检查端点（Dify 兼容）"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": int(time.time() - self.server_start_time),
                "tools_registered": len(self.tool_registry.get_all_tools()),
                "server": "AnmeiSmart MCP Server",
                "version": "1.0.0",
                "protocols": ["JSON-RPC 2.0", "HTTP REST"]
            }

    def _discover_and_register_tools(self):
        """自动发现并注册工具模块"""
        try:
            # 导入工具模块，触发装饰器注册
            import app.mcp.tools
            
            # 记录注册结果
            tools_count = len(self.tool_registry.get_all_tools())
            categories = self.tool_registry.get_all_categories()
            
            logger.info(f"工具发现完成: 注册了 {tools_count} 个工具")
            logger.info(f"工具分类: {', '.join(categories)}")
            
            # 按分类记录工具
            for category in categories:
                category_tools = self.tool_registry.get_tools_by_category(category)
                logger.debug(f"分类 '{category}': {', '.join(category_tools)}")
                
        except Exception as e:
            logger.error(f"工具发现失败: {e}")


# 全局MCP服务器实例
mcp_server = None

def get_mcp_server() -> UnifiedMCPServer:
    """获取MCP服务器实例（单例模式）"""
    global mcp_server
    if mcp_server is None:
        mcp_server = UnifiedMCPServer()
    return mcp_server

def create_mcp_app() -> FastAPI:
    """创建MCP应用"""
    server = get_mcp_server()
    return server.app

# 启动脚本
if __name__ == "__main__":
    import uvicorn
    app = create_mcp_app()
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info") 