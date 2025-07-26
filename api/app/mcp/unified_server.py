"""
统一MCP服务器 - 模块化架构

核心框架，负责：
- 服务器启动和路由管理
- 请求分发和响应处理
- 组件协调和生命周期管理

工具实现完全分离到独立模块中，遵循单一职责原则
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session
import logging

from app.mcp.registry import get_global_registry
from app.mcp.middleware import MCPAuthenticator, MCPMiddleware, MCPLoggingMiddleware
from app.services.mcp_group_service import MCPGroupService

logger = logging.getLogger(__name__)


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

        @self.app.get("/health")
        async def health_check():
            """健康检查端点"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": int(time.time() - self.server_start_time),
                "tools_registered": len(self.tool_registry.get_all_tools())
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