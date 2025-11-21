"""MCP服务层，处理工具发现、执行和会话管理"""
import asyncio
import logging
import time
from tokenize import Token
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from app.mcp.infrastructure.db.mcp import MCPToolGroup, MCPTool, MCPCallLog
from app.mcp.types import Tool, ServerCapabilities, ToolsCapability, Implementation, SERVER_LATEST_PROTOCOL_VERSION
from app.mcp.utils import MCPSession, generate_token
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class MCPToolDiscoveryService:
    """MCP工具发现服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_tools_by_server_code(self, server_code: str) -> List[Tool]:
        """根据server_code获取工具列表"""
        try:
            # 查询工具分组
            group = self.db.query(MCPToolGroup).filter(
                MCPToolGroup.server_code == server_code,
                MCPToolGroup.enabled == True
            ).first()
            
            if not group:
                logger.warning(f"未找到启用的工具分组，server_code: {server_code}")
                return []
            
            # 查询该分组下的启用工具
            mcp_tools = self.db.query(MCPTool).filter(
                MCPTool.group_id == group.id,
                MCPTool.enabled == True
            ).all()
            
            tools = []
            for mcp_tool in mcp_tools:
                tool = Tool(
                    name=mcp_tool.tool_name,
                    description=mcp_tool.description or f"{mcp_tool.tool_name} 工具",
                    inputSchema=self._generate_input_schema(mcp_tool)
                )
                tools.append(tool)
            
            logger.info(f"发现 {len(tools)} 个工具，server_code: {server_code}")
            return tools
            
        except Exception as e:
            logger.error(f"工具发现失败，server_code: {server_code}, 错误: {e}")
            return []
    
    def get_group_by_server_code(self, server_code: str) -> Optional[MCPToolGroup]:
        """根据server_code获取工具分组"""
        try:
            return self.db.query(MCPToolGroup).filter(
                MCPToolGroup.server_code == server_code,
                MCPToolGroup.enabled == True
            ).first()
        except Exception as e:
            logger.error(f"查询工具分组失败，server_code: {server_code}, 错误: {e}")
            return None
    
    def _generate_input_schema(self, mcp_tool: MCPTool) -> Dict[str, Any]:
        """为MCP工具生成输入Schema"""
        # 基础Schema结构
        base_schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        # 从配置数据中提取参数定义
        config_data = mcp_tool.config_data or {}
        
        if "parameters" in config_data:
            for param_name, param_config in config_data["parameters"].items():
                base_schema["properties"][param_name] = {
                    "type": param_config.get("type", "string"),
                    "description": param_config.get("description", f"{param_name} 参数")
                }
                
                if param_config.get("required", False):
                    base_schema["required"].append(param_name)
                
                # 添加枚举值
                if "enum" in param_config:
                    base_schema["properties"][param_name]["enum"] = param_config["enum"]
        else:
            # 默认提供一个通用的文本输入参数
            base_schema["properties"]["query"] = {
                "type": "string",
                "description": "输入查询或命令文本"
            }
            base_schema["required"] = ["query"]
        
        return base_schema


class MCPToolExecutionService:
    """MCP工具执行服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def execute_tool(
        self, 
        server_code: str, 
        tool_name: str, 
        arguments: Dict[str, Any],
        caller_app_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """执行MCP工具"""
        start_time = time.time()
        success = False
        error_message = None
        result = None
        
        try:
            # 查询工具分组
            group = self.db.query(MCPToolGroup).filter(
                MCPToolGroup.server_code == server_code,
                MCPToolGroup.enabled == True
            ).first()
            
            if not group:
                raise ValueError(f"未找到启用的工具分组: {server_code}")
            
            # 查询具体工具
            tool = self.db.query(MCPTool).filter(
                MCPTool.group_id == group.id,
                MCPTool.tool_name == tool_name,
                MCPTool.enabled == True
            ).first()
            
            if not tool:
                raise ValueError(f"未找到启用的工具: {tool_name}")
            
            # 执行工具逻辑
            result = await self._execute_tool_logic(tool, arguments)
            success = True
            
            logger.info(f"工具执行成功: {tool_name}, 耗时: {(time.time() - start_time) * 1000:.2f}ms")
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"工具执行失败: {tool_name}, 错误: {error_message}")
            
        finally:
            # 记录调用日志
            duration_ms = int((time.time() - start_time) * 1000)
            await self._log_tool_call(
                tool_name=tool_name,
                group_id=group.id if 'group' in locals() else None,
                caller_app_id=caller_app_id,
                request_data=arguments,
                response_data=result,
                success=success,
                error_message=error_message,
                duration_ms=duration_ms
            )
        
        if not success:
            raise Exception(error_message)
            
        return result
    
    async def _execute_tool_logic(self, tool: MCPTool, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行具体的工具逻辑"""
        # 这里是工具执行的核心逻辑
        # 根据工具类型调用相应的执行器
        
        tool_name = tool.tool_name
        config_data = tool.config_data or {}
        
        # 基于工具名称的简单路由
        if tool_name == "echo_tool":
            # 特殊处理回显工具
            message = arguments.get("message", "No message provided")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Echo: {message}"
                    }
                ]
            }
        elif tool_name.startswith("user_"):
            return await self._execute_user_tool(tool, arguments)
        elif tool_name.startswith("customer_"):
            return await self._execute_customer_tool(tool, arguments)
        elif tool_name.startswith("treatment_"):
            return await self._execute_treatment_tool(tool, arguments)
        elif tool_name.startswith("project_"):
            return await self._execute_project_tool(tool, arguments)
        else:
            # 默认处理：通用工具
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"工具 {tool_name} 执行成功\n参数: {arguments}\n配置: {config_data}"
                    }
                ]
            }
    
    async def _execute_user_tool(self, tool: MCPTool, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行用户相关工具"""
        from app.mcp.tools.user.profile import get_user_profile
        from app.mcp.tools.user.search import search_users
        
        tool_name = tool.tool_name
        
        if tool_name == "user_profile":
            return await get_user_profile(arguments)
        elif tool_name == "user_search":
            return await search_users(arguments)
        else:
            return {"content": [{"type": "text", "text": f"未知的用户工具: {tool_name}"}]}
    
    async def _execute_customer_tool(self, tool: MCPTool, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行客户相关工具"""
        from app.mcp.tools.customer.analysis import analyze_customer
        from app.mcp.tools.customer.preferences import get_customer_preferences
        
        tool_name = tool.tool_name
        
        if tool_name == "customer_analysis":
            return await analyze_customer(arguments)
        elif tool_name == "customer_preferences":
            return await get_customer_preferences(arguments)
        else:
            return {"content": [{"type": "text", "text": f"未知的客户工具: {tool_name}"}]}
    
    async def _execute_treatment_tool(self, tool: MCPTool, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行治疗相关工具"""
        from app.mcp.tools.treatment.plan_generation import generate_treatment_plan
        from app.mcp.tools.treatment.optimization import optimize_treatment
        
        tool_name = tool.tool_name
        
        if tool_name == "treatment_plan_generation":
            return await generate_treatment_plan(arguments)
        elif tool_name == "treatment_optimization":
            return await optimize_treatment(arguments)
        else:
            return {"content": [{"type": "text", "text": f"未知的治疗工具: {tool_name}"}]}
    
    async def _execute_project_tool(self, tool: MCPTool, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行项目相关工具"""
        from app.mcp.tools.projects.service_info import get_service_info
        
        tool_name = tool.tool_name
        
        if tool_name == "project_service_info":
            return await get_service_info(arguments)
        else:
            return {"content": [{"type": "text", "text": f"未知的项目工具: {tool_name}"}]}
    
    async def _log_tool_call(
        self,
        tool_name: str,
        group_id: Optional[str],
        caller_app_id: Optional[str],
        request_data: Dict[str, Any],
        response_data: Optional[Dict[str, Any]],
        success: bool,
        error_message: Optional[str],
        duration_ms: int
    ):
        """记录工具调用日志"""
        try:
            log = MCPCallLog(
                tool_name=tool_name,
                group_id=group_id,
                caller_app_id=caller_app_id,
                request_data=request_data,
                response_data=response_data,
                success=success,
                error_message=error_message,
                duration_ms=duration_ms
            )
            self.db.add(log)
            self.db.commit()
        except Exception as e:
            logger.error(f"记录工具调用日志失败: {e}")
            self.db.rollback()


class MCPSessionManager:
    """MCP会话管理器"""
    
    def __init__(self):
        self.sessions: Dict[str, MCPSession] = {}
        self.session_queues: Dict[str, asyncio.Queue] = {}
    
    def create_session(self, api_key: str) -> str:
        """创建新的MCP会话"""
        session_id = generate_token("sess", 16)
        session = MCPSession(session_id, api_key)
        self.sessions[session_id] = session
        self.session_queues[session_id] = asyncio.Queue()
        
        logger.info(f"创建MCP会话: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[MCPSession]:
        """获取会话"""
        return self.sessions.get(session_id)
    
    def get_session_queue(self, session_id: str) -> Optional[asyncio.Queue]:
        """获取会话消息队列"""
        return self.session_queues.get(session_id)
    
    def update_session_ping(self, session_id: str):
        """更新会话ping时间"""
        session = self.sessions.get(session_id)
        if session:
            session.update_ping()
    
    def remove_session(self, session_id: str):
        """移除会话"""
        self.sessions.pop(session_id, None)
        self.session_queues.pop(session_id, None)
        logger.info(f"移除MCP会话: {session_id}")
    
    def cleanup_expired_sessions(self, timeout_seconds: int = 3600):
        """清理过期会话"""
        expired_sessions = []
        for session_id, session in self.sessions.items():
            if session.is_expired(timeout_seconds):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.remove_session(session_id)
        
        if expired_sessions:
            logger.info(f"清理了 {len(expired_sessions)} 个过期会话")
    
    def get_server_capabilities(self) -> ServerCapabilities:
        """获取服务器能力"""
        return ServerCapabilities(
            tools=ToolsCapability(listChanged=True),
            experimental={"anmei_smart": {"version": "1.0.0"}}
        )
    
    def get_server_info(self) -> Implementation:
        """获取服务器信息"""
        return Implementation(
            name="AnmeiSmart MCP Server",
            version="1.0.0"
        )
