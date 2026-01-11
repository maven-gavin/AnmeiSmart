"""MCP Server端点实现"""
import asyncio
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, Response, Depends, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.common.deps import get_db
from app.mcp.oauth import oauth2_manager
from app.mcp.services import MCPToolDiscoveryService, MCPToolExecutionService, MCPSessionManager
from app.mcp.utils import create_mcp_error_response, create_mcp_success_response
from app.mcp import types

logger = logging.getLogger(__name__)
router = APIRouter()

# 全局会话管理器
session_manager = MCPSessionManager()

MCP_SESSION_ID = "X-MCP-Session-ID"


async def send_response_to_sse(session_id: str, response: JSONResponse) -> bool:
    """将响应发送到SSE流，返回是否成功发送"""
    try:
        queue = session_manager.get_session_queue(session_id)
        if queue:
            # 获取响应内容
            content = response.body.decode() if hasattr(response, 'body') else str(response)
            await queue.put(content)
            logger.info(f"响应已发送到SSE流: {session_id}")
            return True
        else:
            logger.info(f"会话无SSE连接，跳过发送: {session_id}")
            return False
    except Exception as e:
        logger.error(f"发送响应到SSE流失败: {e}")
        return False


async def require_bearer_token(request: Request) -> str:
    """验证Bearer令牌"""
    logger.info(f"开始验证Bearer令牌")
    logger.info(f"Authorization头部: {request.headers.get('Authorization', 'None')}")
    
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        logger.warning("Authorization头部格式错误，缺少Bearer前缀")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    
    token = auth.split(" ", 1)[1].strip()
    logger.info(f"提取的token: {token[:10] if token else 'None'}...")

    api_key = oauth2_manager.get_api_key_by_token(token)
    logger.info(f"通过token获取的api_key: {api_key[:10] if api_key else 'None'}...")

    if not api_key:
        logger.warning("无效的token，无法获取api_key")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    logger.info(f"Bearer令牌验证成功")
    return token


# ===== MCP Server Endpoints =====

@router.get("/server/info")
async def get_server_info():
    """获取MCP服务器基本信息"""
    logger.info("=" * 80)
    logger.info("收到MCP服务器信息请求")
    
    try:
        server_info = session_manager.get_server_info()
        capabilities = session_manager.get_server_capabilities()
        
        logger.info(f"服务器信息对象类型: {type(server_info)}")
        logger.info(f"服务器能力对象类型: {type(capabilities)}")
        logger.info(f"服务器信息原始对象: {server_info}")
        logger.info(f"服务器能力原始对象: {capabilities}")
        
        # Pydantic V2: 使用 model_dump() 方法（推荐方式）
        # model_dump() 是 V2 的标准方法，性能更好，支持更多选项
        # 使用 mode='json' 确保所有值都是 JSON 可序列化的
        server_info_dict = server_info.model_dump(mode='json')
        capabilities_dict = capabilities.model_dump(mode='json')
        
        logger.info(f"服务器信息字典: {server_info_dict}")
        logger.info(f"服务器能力字典: {capabilities_dict}")
        
        response_data = {
            "server": server_info_dict,
            "capabilities": capabilities_dict,
            "status": "running",
            "protocol_version": types.SERVER_LATEST_PROTOCOL_VERSION
        }
        
        logger.info(f"最终响应数据: {response_data}")
        logger.info("=" * 80)
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"获取MCP服务器信息失败: {e}", exc_info=True)
        logger.error(f"错误类型: {type(e)}")
        logger.error(f"错误详情: {str(e)}")
        logger.error("=" * 80)
        return JSONResponse(
            content={"error": f"Failed to get server info: {str(e)}"},
            status_code=500
        )


@router.options("/server/{server_code}/mcp")
async def mcp_options(request: Request, server_code: str):
    """MCP端点OPTIONS处理"""
    logger.info(f"收到MCP OPTIONS请求 - server_code: {server_code}")
    logger.info(f"请求头信息: {dict(request.headers)}")
    
    response_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, X-MCP-Session-ID, X-MCP-Prefer-Streaming, Accept",
        "Access-Control-Max-Age": "86400"
    }
    
    logger.info(f"OPTIONS响应头: {response_headers}")
    
    response = Response(
        status_code=200,
        headers=response_headers
    )
    
    logger.info(f"OPTIONS响应: status_code={response.status_code}")
    return response


@router.get("/server/{server_code}/mcp")
async def mcp_get(request: Request, server_code: str):
    """MCP SSE端点 - 支持StreamableHttp连接"""
    logger.info(f"收到MCP SSE连接请求 - server_code: {server_code}")
    logger.info(f"请求头信息: {dict(request.headers)}")
    
    session_id = request.headers.get(MCP_SESSION_ID)
    logger.info(f"请求头中的session_id: {session_id}")
    
    # 如果没有session_id, Initialize 方法会创建会话失败
    if not session_id:
        logger.info("未找到session_id，Initialize 方法会创建会话失败")
        error_response = JSONResponse({"detail": "Missing session_id"}, status_code=404)
        logger.info(f"返回错误响应: {error_response.status_code} - {error_response.body.decode() if hasattr(error_response, 'body') else 'No body'}")
        return error_response
    
    session = session_manager.get_session(session_id)
    if not session:
        logger.warning(f"会话不存在: {session_id}")
        error_response = JSONResponse({"detail": "unknown session_id"}, status_code=404)
        logger.info(f"返回错误响应: {error_response.status_code} - {error_response.body.decode() if hasattr(error_response, 'body') else 'No body'}")
        return error_response
    
    logger.info(f"会话验证成功: {session_id}")
    logger.info(f"会话详情: api_key={session.api_key[:10] if session.api_key else 'None'}..., created_at={session.created_at}")

    async def event_generator():
        logger.info(f"开始SSE事件生成器 - session_id: {session_id}")
        try:
            queue = session_manager.get_session_queue(session_id)
            if not queue:
                logger.warning(f"会话队列不存在: {session_id}")
                return
            
            logger.info(f"获取到会话队列: {session_id}")
            
            logger.info(f"开始SSE消息循环 - session_id: {session_id}")
            while True:
                if await request.is_disconnected():
                    logger.info(f"客户端断开连接 - session_id: {session_id}")
                    break
                
                try:
                    # 等待消息或超时
                    logger.debug(f"等待队列消息 - session_id: {session_id}")
                    message = await asyncio.wait_for(queue.get(), timeout=15.0)
                    logger.info(f"收到队列消息 - session_id: {session_id}, 消息类型: {type(message)}")
                    
                    # 确保消息是JSON-RPC格式
                    if isinstance(message, str):
                        try:
                            # 尝试解析为JSON，如果不是JSON-RPC格式，包装它
                            import json
                            parsed = json.loads(message)
                            if "jsonrpc" not in parsed:
                                # 包装为JSON-RPC格式
                                logger.debug(f"包装非JSON-RPC消息为JSON-RPC格式 - session_id: {session_id}")
                                message = json.dumps({
                                    "jsonrpc": "2.0",
                                    "id": None,
                                    "result": parsed
                                })
                        except json.JSONDecodeError:
                            # 如果不是JSON，包装为文本结果
                            logger.debug(f"包装非JSON消息为文本结果 - session_id: {session_id}")
                            message = json.dumps({
                                "jsonrpc": "2.0",
                                "id": None,
                                "result": {"content": message}
                            })
                    
                    logger.debug(f"发送SSE消息 - session_id: {session_id}")
                    yield f"data: {message}\n\n"
                    
                except asyncio.TimeoutError:
                    # 发送心跳
                    logger.debug(f"发送SSE心跳 - session_id: {session_id}")
                    yield f": ping\n\n"
                    session_manager.update_session_ping(session_id)
                    
        except Exception as e:
            logger.error(f"SSE连接错误 - session_id: {session_id}, 错误: {e}")
            # 发送错误响应
            error_msg = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            yield f"data: {JSONResponse(content=error_msg).body.decode()}\n\n"
        finally:
            logger.info(f"SSE连接关闭 - session_id: {session_id}")
            # 如果是新创建的会话，清理会话
            if not request.headers.get(MCP_SESSION_ID):
                logger.info(f"清理新创建的会话 - session_id: {session_id}")
                session_manager.remove_session(session_id)

    response_headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, X-MCP-Session-ID, X-MCP-Prefer-Streaming, Accept"
    }
    
    logger.info(f"创建SSE响应 - session_id: {session_id}, headers: {response_headers}")
    
    return StreamingResponse(
        event_generator(), 
        media_type="text/event-stream",
        headers=response_headers
    )


@router.post("/server/{server_code}/mcp")
async def mcp_post(
    request: Request, 
    server_code: str, 
    token: str = Depends(require_bearer_token),
    db: Session = Depends(get_db)
):
    """MCP请求处理端点"""
    logger.info(f"收到MCP POST请求 - server_code: {server_code}")
    logger.info(f"请求头信息: {dict(request.headers)}")
    logger.info(f"认证token: {token[:10] if token else 'None'}...")
    
    session_id = None
    msg_id = None
    
    try:
        body = await request.json()
        logger.info(f"请求体内容: {body}")
        
        msg_id = body.get("id")
        method = (body.get("method") or "").strip()
        params = body.get("params") or {}
        
        logger.info(f"MCP请求详情 - msg_id: {msg_id}, method: {method}, params_keys: {list(params.keys()) if params else []}")
        if params:
            logger.info(f"请求参数详情: {params}")
        
        if not token:
            logger.warning("缺少Authorization头部")
            error_response = JSONResponse({"detail": "Missing authorization header"}, status_code=status.HTTP_401_UNAUTHORIZED)
            logger.info(f"返回认证错误响应: {error_response.status_code}")
            return error_response
        
        
        tool_discovery = MCPToolDiscoveryService(db)
        tool_execution = MCPToolExecutionService(db)
        
        logger.info(f"开始处理MCP方法: {method}")
        
        if method == "initialize":
            api_key = oauth2_manager.get_api_key_by_token(token)
            logger.info(f"处理initialize方法 - api_key: {api_key[:10] if api_key else 'None'}...")
            session_id = session_manager.create_session(api_key)
            logger.info(f"处理initialize方法 - session_id: {session_id}")
            response = await handle_initialize(msg_id, params, api_key, server_code, session_id)
            response.headers[MCP_SESSION_ID] = session_id
            logger.info(f"initialize响应: status_code={response.status_code}, headers={dict(response.headers)}")
            logger.info(f"initialize响应体: {response.body.decode() if hasattr(response, 'body') else 'No body'}")
            return response
        elif method == "notifications/initialized":
            logger.info(f"处理notifications/initialized方法 - session_id: {session_id}")
            response = JSONResponse({}, status_code=202)
            logger.info(f"notifications/initialized响应: status_code={response.status_code}")
            return response
        elif method == "ping":
            logger.info(f"处理ping方法 - session_id: {session_id}")
            response = JSONResponse(create_mcp_success_response(msg_id, {}))
            logger.info(f"ping响应: status_code={response.status_code}, body={response.body.decode() if hasattr(response, 'body') else 'No body'}")
            return response
        elif method == "tools/list":
            logger.info(f"处理tools/list方法 - session_id: {session_id}")
            response = await handle_tools_list(msg_id, params, tool_discovery, server_code)
            logger.info(f"tools/list响应: status_code={response.status_code}, body={response.body.decode() if hasattr(response, 'body') else 'No body'}")
            return response
        elif method == "tools/call":
            logger.info(f"处理tools/call方法 - session_id: {session_id}")
            response = await handle_tools_call(msg_id, params, tool_execution, server_code)
            logger.info(f"tools/call响应: status_code={response.status_code}, body={response.body.decode() if hasattr(response, 'body') else 'No body'}")
            return response
        else:
            logger.warning(f"未知的MCP方法: {method} - session_id: {session_id}")
            response = JSONResponse(
                create_mcp_error_response(msg_id, types.METHOD_NOT_FOUND, f"Unknown method: {method}")
            )
            logger.info(f"未知方法响应: status_code={response.status_code}, body={response.body.decode() if hasattr(response, 'body') else 'No body'}")
            return response
            
    except ValidationError as e:
        logger.error(f"MCP请求验证失败 - session_id: {session_id}, msg_id: {msg_id}, 错误: {e}")
        error_response = JSONResponse(
            create_mcp_error_response(msg_id, types.INVALID_PARAMS, f"Invalid MCP request: {str(e)}")
        )
        # 统一错误处理：如果有会话则发送到SSE流并添加会话头部
        if session_id:
            logger.info(f"发送验证错误到SSE流 - session_id: {session_id}")
            await send_response_to_sse(session_id, error_response)
            if hasattr(error_response, 'headers'):
                error_response.headers[MCP_SESSION_ID] = session_id
        return error_response
    except Exception as e:
        logger.error(f"MCP请求处理失败 - session_id: {session_id}, msg_id: {msg_id}, 错误: {e}")
        error_response = JSONResponse(
            create_mcp_error_response(msg_id, types.INTERNAL_ERROR, f"Internal server error: {str(e)}")
        )
        # 统一错误处理：如果有会话则发送到SSE流并添加会话头部
        if session_id:
            logger.info(f"发送内部错误到SSE流 - session_id: {session_id}")
            await send_response_to_sse(session_id, error_response)
            if hasattr(error_response, 'headers'):
                error_response.headers[MCP_SESSION_ID] = session_id
        return error_response


@router.delete("/server/{server_code}/mcp")
async def mcp_delete(request: Request, server_code: str):
    """MCP会话删除端点"""
    logger.info(f"收到MCP DELETE请求 - server_code: {server_code}")
    logger.info(f"请求头信息: {dict(request.headers)}")
    
    session_id = request.headers.get(MCP_SESSION_ID)
    logger.info(f"要删除的session_id: {session_id}")
    
    if session_id:
        logger.info(f"删除会话: {session_id}")
        session_manager.remove_session(session_id)
        logger.info(f"会话删除完成: {session_id}")
    else:
        logger.warning("未提供session_id，跳过删除操作")
    
    response = JSONResponse({"ok": True})
    logger.info(f"DELETE响应: status_code={response.status_code}, body={response.body.decode() if hasattr(response, 'body') else 'No body'}")
    return response





# ===== MCP Handler Functions =====
async def handle_initialize(
    msg_id: Optional[str | int], 
    params: Dict[str, Any], 
    api_key: str,
    server_code: str,
    session_id: str
) -> JSONResponse:
    """处理初始化请求"""
    logger.info(f"开始处理initialize请求 - msg_id: {msg_id}, server_code: {server_code}, session_id: {session_id}")
    logger.info(f"initialize参数: {params}")
    
    try:
        # 构建初始化结果
        capabilities = session_manager.get_server_capabilities()
        server_info = session_manager.get_server_info()
        instructions = f"MCP服务器已启动，服务代码: {server_code}。您可以调用 tools/list 查看可用工具，使用 tools/call 执行工具。"
        
        logger.info(f"服务器能力: {capabilities}")
        logger.info(f"服务器信息: {server_info}")
        logger.info(f"指令信息: {instructions}")
        
        result = types.InitializeResult(
            protocolVersion=types.SERVER_LATEST_PROTOCOL_VERSION,
            capabilities=capabilities,
            serverInfo=server_info,
            instructions=instructions
        )
        
        result_dict = result.model_dump(by_alias=True, exclude_none=True)
        logger.info(f"初始化结果: {result_dict}")
        
        response = JSONResponse(
            create_mcp_success_response(msg_id, result_dict)
        )
        
        logger.info(f"initialize处理完成 - status_code: {response.status_code}")
        return response
        
    except Exception as e:
        logger.error(f"初始化失败 - msg_id: {msg_id}, 错误: {e}")
        error_response = JSONResponse(
            create_mcp_error_response(msg_id, types.INTERNAL_ERROR, f"Initialize failed: {str(e)}")
        )
        logger.info(f"initialize错误响应: status_code={error_response.status_code}, body={error_response.body.decode() if hasattr(error_response, 'body') else 'No body'}")
        return error_response


async def handle_tools_list(
    msg_id: Optional[str | int],
    params: Dict[str, Any],
    tool_discovery: MCPToolDiscoveryService,
    server_code: str
) -> JSONResponse:
    """处理工具列表请求"""
    logger.info(f"开始处理tools/list请求 - msg_id: {msg_id}, server_code: {server_code}")
    logger.info(f"tools/list参数: {params}")
    
    try:
        logger.info(f"获取server_code={server_code}的工具列表")
        tools = tool_discovery.get_tools_by_server_code(server_code)
        logger.info(f"找到工具数量: {len(tools)}")
        
        for i, tool in enumerate(tools):
            logger.info(f"工具[{i}]: name={tool.name}, description={tool.description[:50] if tool.description else 'None'}...")
        
        tool_dicts = [tool.model_dump(by_alias=True, exclude_none=True) for tool in tools]
        logger.info(f"工具字典列表: {tool_dicts}")
        
        result = types.ListToolsResult(tools=tool_dicts)
        result_dict = result.model_dump(by_alias=True, exclude_none=True)
        logger.info(f"工具列表结果: {result_dict}")
        
        response = JSONResponse(
            create_mcp_success_response(msg_id, result_dict)
        )
        
        logger.info(f"tools/list处理完成 - status_code: {response.status_code}")
        return response
        
    except Exception as e:
        logger.error(f"获取工具列表失败 - msg_id: {msg_id}, server_code: {server_code}, 错误: {e}")
        error_response = JSONResponse(
            create_mcp_error_response(msg_id, types.INTERNAL_ERROR, f"List tools failed: {str(e)}")
        )
        logger.info(f"tools/list错误响应: status_code={error_response.status_code}, body={error_response.body.decode() if hasattr(error_response, 'body') else 'No body'}")
        return error_response


async def handle_tools_call(
    msg_id: Optional[str | int],
    params: Dict[str, Any],
    tool_execution: MCPToolExecutionService,
    server_code: str
) -> JSONResponse:
    """处理工具调用请求"""
    logger.info(f"开始处理tools/call请求 - msg_id: {msg_id}, server_code: {server_code}")
    logger.info(f"tools/call参数: {params}")
    
    try:
        tool_name = params.get("name")
        arguments = params.get("arguments") or {}
        
        logger.info(f"工具名称: {tool_name}")
        logger.info(f"工具参数: {arguments}")
        
        if not tool_name:
            logger.warning(f"缺少工具名称 - msg_id: {msg_id}")
            error_response = JSONResponse(
                create_mcp_error_response(msg_id, types.INVALID_PARAMS, "Tool name is required")
            )
            logger.info(f"tools/call参数错误响应: status_code={error_response.status_code}, body={error_response.body.decode() if hasattr(error_response, 'body') else 'No body'}")
            return error_response
        
        # 执行工具
        caller_app_id = f"mcp_client_{server_code}"
        logger.info(f"执行工具 - tool_name: {tool_name}, server_code: {server_code}, caller_app_id: {caller_app_id}")
        
        result = await tool_execution.execute_tool(
            server_code=server_code,
            tool_name=tool_name,
            arguments=arguments,
            caller_app_id=caller_app_id
        )
        
        logger.info(f"工具执行结果: {result}")
        
        # 确保返回的内容符合MCP规范
        content = result.get("content", [{"type": "text", "text": str(result)}])
        logger.info(f"工具执行内容: {content}")
        
        call_result = types.CallToolResult(
            content=content,
            isError=False
        )
        
        result_dict = call_result.model_dump(by_alias=True, exclude_none=True)
        logger.info(f"工具调用结果: {result_dict}")
        
        response = JSONResponse(
            create_mcp_success_response(msg_id, result_dict)
        )
        
        logger.info(f"tools/call处理完成 - status_code: {response.status_code}")
        return response
        
    except Exception as e:
        logger.error(f"工具调用失败 - msg_id: {msg_id}, tool_name: {tool_name if 'tool_name' in locals() else 'Unknown'}, 错误: {e}")
        
        # 返回错误结果
        error_content = [{"type": "text", "text": f"工具执行失败: {str(e)}"}]
        logger.info(f"工具执行错误内容: {error_content}")
        
        error_result = types.CallToolResult(
            content=error_content,
            isError=True
        )
        
        result_dict = error_result.model_dump(by_alias=True, exclude_none=True)
        logger.info(f"工具调用错误结果: {result_dict}")
        
        response = JSONResponse(
            create_mcp_success_response(msg_id, result_dict)
        )
        
        logger.info(f"tools/call错误处理完成 - status_code: {response.status_code}")
        return response
