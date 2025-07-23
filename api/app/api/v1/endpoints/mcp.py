"""
MCP服务API端点

提供对新架构MCP服务器的HTTP访问接口，
支持工具列表查询、工具调用等功能。
"""
import logging
import json
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, Body
from pydantic import BaseModel

from app.mcp.server import mcp_server
# 确保工具被注册
import app.mcp.tools

router = APIRouter()
logger = logging.getLogger(__name__)


class MCPToolCallRequest(BaseModel):
    """MCP工具调用请求模型"""
    tool_name: str
    arguments: Dict[str, Any] = {}


class MCPResponse(BaseModel):
    """MCP响应模型"""
    success: bool
    data: Any = None
    error: str = None


@router.get("/tools", response_model=MCPResponse)
async def get_mcp_tools():
    """
    获取可用的MCP工具列表
    
    Returns:
        包含工具列表的响应
    """
    try:
        tools = mcp_server.get_available_tools()
        
        return MCPResponse(
            success=True,
            data={
                "tools": tools,
                "server_info": mcp_server.server_info,
                "total_tools": len(tools)
            }
        )
        
    except Exception as e:
        logger.error(f"获取MCP工具列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get MCP tools: {str(e)}"
        )


@router.post("/tools/call", response_model=MCPResponse)
async def call_mcp_tool(request: MCPToolCallRequest):
    """
    调用指定的MCP工具
    
    Args:
        request: 工具调用请求，包含工具名称和参数
    
    Returns:
        工具执行结果
    """
    try:
        logger.info(f"调用MCP工具: {request.tool_name}, arguments: {request.arguments}")
        
        # 调用工具
        result = await mcp_server.call_tool(request.tool_name, request.arguments)
        
        return MCPResponse(
            success=True,
            data=result
        )
        
    except ValueError as e:
        # 工具不存在或参数错误
        logger.warning(f"MCP工具调用参数错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"MCP工具调用失败: tool={request.tool_name}, error={e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tool execution failed: {str(e)}"
        )


@router.post("/jsonrpc")
async def handle_jsonrpc_request(request: Dict[str, Any]):
    """
    处理JSON-RPC 2.0请求（兼容MCP协议）
    
    Args:
        request: JSON-RPC请求字典
    
    Returns:
        JSON-RPC响应字典
    """
    try:
        logger.info(f"处理JSON-RPC请求: {str(request)[:200]}...")
        
        # 将字典转为JSON字符串传递给MCP服务器
        request_body = json.dumps(request)
        response_str = await mcp_server.handle_request(request_body)
        
        # 将响应字符串转回字典返回
        return json.loads(response_str)
        
    except Exception as e:
        logger.error(f"JSON-RPC请求处理失败: {e}", exc_info=True)
        # 返回标准JSON-RPC错误响应
        return {
            "jsonrpc": "2.0",
            "id": request.get("id") if isinstance(request, dict) else None,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }


@router.get("/status", response_model=MCPResponse)
async def get_mcp_status():
    """
    获取MCP服务器状态信息
    
    Returns:
        服务器状态和统计信息
    """
    try:
        status_info = {
            "server_info": mcp_server.server_info,
            "total_tools": len(mcp_server.tools),
            "available_tools": list(mcp_server.tools.keys()),
            "status": "running"
        }
        
        return MCPResponse(
            success=True,
            data=status_info
        )
        
    except Exception as e:
        logger.error(f"获取MCP状态失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get MCP status: {str(e)}"
        ) 