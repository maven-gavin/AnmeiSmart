from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import httpx
import logging

from app.common.deps import get_db
from app.mcp.mcp_group_service import MCPGroupService
from app.mcp.schemas.mcp import (
    MCPGroupCreate,
    MCPGroupUpdate,
    MCPGroupInfo,
    MCPGroupListResponse,
    MCPGroupSingleResponse,
    MCPApiKeyResponse,
    MCPServerUrlResponse,
    MCPSuccessResponse,
    MCPErrorResponse,
    MCPServerStatusResponse,
    MCPToolListResponse,
    MCPToolSingleResponse,
    MCPToolUpdate
)
from app.identity_access.deps import get_current_admin
from app.identity_access.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()

# ==================== MCP分组管理API ====================

@router.get("/groups", response_model=MCPGroupListResponse)
async def get_mcp_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """获取MCP工具分组列表 - Controller层"""
    groups = await MCPGroupService.get_all_groups(db)
    return MCPGroupListResponse(
        success=True,
        data=groups,
        message="获取MCP分组列表成功"
    )


@router.get("/groups/{group_id}", response_model=MCPGroupSingleResponse)
async def get_mcp_group(
    group_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """获取单个MCP分组详情 - Controller层"""
    group = await MCPGroupService.get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP分组不存在"
        )
    
    return MCPGroupSingleResponse(
        success=True,
        data=group,
        message="获取MCP分组详情成功"
    )


@router.post("/groups", response_model=MCPGroupSingleResponse)
async def create_mcp_group(
    group_create: MCPGroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """创建MCP工具分组 - Controller层"""
    group = await MCPGroupService.create_group(db, group_create, str(current_user.id))
    
    logger.info(f"管理员 {current_user.id} 创建了MCP分组: {group_create.name}")
    
    return MCPGroupSingleResponse(
        success=True,
        data=group,
        message="MCP分组创建成功"
    )


@router.put("/groups/{group_id}", response_model=MCPGroupSingleResponse)
async def update_mcp_group(
    group_id: str,
    group_update: MCPGroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """更新MCP分组信息 - Controller层"""
    group = await MCPGroupService.update_group(db, group_id, group_update)
    
    logger.info(f"管理员 {current_user.id} 更新了MCP分组: {group_id}")
    
    return MCPGroupSingleResponse(
        success=True,
        data=group,
        message="MCP分组更新成功"
    )


@router.delete("/groups/{group_id}", response_model=MCPSuccessResponse)
async def delete_mcp_group(
    group_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """删除MCP分组 - Controller层"""
    success = await MCPGroupService.delete_group(db, group_id)
    
    if success:
        logger.warning(f"管理员 {current_user.id} 删除了MCP分组: {group_id}")
        return MCPSuccessResponse(
            success=True,
            message="MCP分组删除成功"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP分组不存在"
        )


# ==================== API密钥管理API ====================

@router.get("/groups/{group_id}/api-key", response_model=MCPApiKeyResponse)
async def get_group_api_key(
    group_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """查看分组API Key（管理员专用）- Controller层"""
    api_key = await MCPGroupService.get_group_api_key(db, group_id)
    
    logger.info(f"管理员 {current_user.id} 查看了分组 {group_id} 的API密钥")
    
    return MCPApiKeyResponse(
        success=True,
        data={"api_key": api_key},
        message="API密钥获取成功"
    )


@router.post("/groups/{group_id}/regenerate-key", response_model=MCPApiKeyResponse)
async def regenerate_group_api_key(
    group_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """重新生成分组API Key - Controller层"""
    new_api_key = await MCPGroupService.regenerate_api_key(db, group_id, str(current_user.id))
    
    logger.warning(f"管理员 {current_user.id} 重新生成了分组 {group_id} 的API密钥")
    
    return MCPApiKeyResponse(
        success=True,
        data={"api_key": new_api_key},
        message="API密钥重新生成成功"
    )


@router.get("/groups/{group_id}/server-url", response_model=MCPServerUrlResponse)
async def get_group_server_url(
    group_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """获取分组的完整MCP Server URL（管理员专用）- Controller层"""
    # 确保分组有server_code，如果没有则生成
    server_code = await MCPGroupService.ensure_server_code(db, group_id)
    
    # 获取完整的MCP Server URL
    server_url = await MCPGroupService.get_group_server_url(db, group_id)
    
    logger.info(f"管理员 {current_user.id} 获取了分组 {group_id} 的MCP Server URL")
    
    return MCPServerUrlResponse(
        success=True,
        data={
            "server_url": server_url,
            "server_code": server_code
        },
        message="MCP Server URL获取成功"
    )


# ==================== MCP工具管理API ====================

@router.get("/tools", response_model=MCPToolListResponse)
async def get_mcp_tools(
    group_id: Optional[str] = Query(None, description="按分组筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """获取MCP工具列表 - Controller层"""
    tools = await MCPGroupService.get_tools(db, group_id=group_id)
    return MCPToolListResponse(
        success=True,
        data=tools,
        message="获取MCP工具列表成功"
    )


@router.put("/tools/{tool_id}", response_model=MCPToolSingleResponse)
async def update_mcp_tool(
    tool_id: str,
    tool_update: MCPToolUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """更新MCP工具配置 - Controller层"""
    tool = await MCPGroupService.update_tool(db, tool_id, tool_update)
    
    logger.info(f"管理员 {current_user.id} 更新了MCP工具: {tool_id}")
    
    return MCPToolSingleResponse(
        success=True,
        data=tool,
        message="MCP工具更新成功"
    )


@router.post("/tools/refresh", response_model=MCPSuccessResponse)
async def refresh_mcp_tools(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """刷新MCP工具列表 - Controller层"""
    
    try:
        # 尝试从MCP服务器获取最新工具信息
        mcp_tools_info = await _get_mcp_tools_from_server()
        
        if not mcp_tools_info:
            logger.warning("无法从MCP服务器获取工具信息，返回成功但工具数为0")
            return MCPSuccessResponse(
                success=True,
                message="MCP工具列表刷新完成，但未发现新工具（服务器可能未启动）"
            )
        
        # 同步到数据库
        updated_count = await MCPGroupService.sync_tools_from_mcp_server(db, mcp_tools_info)
        
        logger.info(f"管理员 {current_user.id} 刷新了MCP工具列表，更新了 {updated_count} 个工具")
        
        return MCPSuccessResponse(
            success=True,
            message=f"MCP工具列表刷新成功，发现并同步了 {len(mcp_tools_info)} 个工具，更新了 {updated_count} 个工具"
        )
        
    except Exception as e:
        logger.error(f"刷新MCP工具列表失败: {e}")
        return MCPSuccessResponse(
            success=True,
            message="MCP工具列表刷新遇到问题，但系统仍正常运行。请检查MCP服务器状态或联系管理员。"
        )


# ==================== 统一MCP服务器集成API ====================

@router.get("/server/status", response_model=MCPServerStatusResponse)
async def get_mcp_server_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """获取统一MCP服务器真实状态 - Controller层"""
    
    # 调用统一MCP Server获取真实状态
    mcp_status = await _check_mcp_server_health()
    
    # 获取数据库中的分组统计
    groups = await MCPGroupService.get_all_groups(db)
    
    server_status = {
        "status": mcp_status.get("status", "unknown"),
        "server": mcp_status.get("server_info", {}),
        "tools_count": mcp_status.get("total_tools", 0),
        "groups_count": len(groups),
        "last_check": "2025-01-27",
        "unified_server": True,
        "endpoint": "http://localhost:8000/mcp"
    }
    
    return MCPServerStatusResponse(
        success=True,
        data=server_status,
        message="获取MCP服务器状态成功"
    )


@router.get("/dify-config")
async def generate_dify_mcp_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """生成Dify兼容的MCP配置 - Controller层"""
    groups = await MCPGroupService.get_all_groups(db)
    
    dify_config = await _build_dify_config(groups)
    
    logger.info(f"管理员 {current_user.id} 生成了Dify MCP配置")
    
    return {
        "success": True,
        "data": {
            "mcp_config": dify_config,
            "total_groups": len(dify_config),
            "server_url": "http://127.0.0.1:8000/api/v1/mcp/jsonrpc",
            "protocol": "sse+jsonrpc",
            "generated_at": "2025-01-27"
        },
        "message": "Dify MCP配置生成成功"
    }


# ==================== 私有辅助函数 ====================

async def _check_mcp_server_health() -> dict:
    """检查MCP服务器健康状态 - 私有辅助函数"""
    try:
        async with httpx.AsyncClient() as client:
            # 使用完整的API路径，包含 /api/v1 前缀
            response = await client.get("http://localhost:8000/api/v1/mcp/server/info", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                # 适配响应格式，提取服务器信息
                return {
                    "status": data.get("status", "running"),
                    "server_info": data.get("server", {}),
                    "total_tools": data.get("capabilities", {}).get("tools", {}).get("listChanged", False) if data.get("capabilities") else 0
                }
            else:
                raise Exception(f"MCP Server返回错误: {response.status_code}")
    except httpx.HTTPStatusError as e:
        logger.warning(f"无法连接到统一MCP Server: HTTP {e.response.status_code}")
        return {
            "status": "offline",
            "error": f"HTTP {e.response.status_code}",
            "server_info": {
                "name": "AnmeiSmart Unified MCP Server",
                "version": "unknown"
            },
            "total_tools": 0
        }
    except httpx.RequestError as e:
        logger.warning(f"无法连接到统一MCP Server: 请求错误 - {e}")
        return {
            "status": "offline",
            "error": str(e),
            "server_info": {
                "name": "AnmeiSmart Unified MCP Server",
                "version": "unknown"
            },
            "total_tools": 0
        }
    except Exception as e:
        logger.warning(f"无法连接到统一MCP Server: {e}")
        return {
            "status": "offline",
            "error": str(e),
            "server_info": {
                "name": "AnmeiSmart Unified MCP Server",
                "version": "unknown"
            },
            "total_tools": 0
        }


async def _get_mcp_tools_from_server() -> List[dict]:
    """从统一MCP Server获取工具列表 - 私有辅助函数"""
    try:
        # 直接从MCP服务器的工具注册表获取工具信息
        from app.mcp.registry import get_mcp_server
        mcp_server = get_mcp_server()
        
        all_tools = []
        for tool_name in mcp_server.tool_registry.get_all_tools():
            metadata = mcp_server.tool_registry.get_tool_metadata(tool_name)
            all_tools.append({
                "name": tool_name,
                "description": metadata.description,
                "category": metadata.category,
                "module": metadata.module
            })
        
        logger.info(f"从MCP工具注册表获取到 {len(all_tools)} 个工具")
        return all_tools
        
    except Exception as e:
        logger.warning(f"无法从统一MCP Server获取工具列表: {e}")
        return []


async def _build_dify_config(groups: List[MCPGroupInfo]) -> dict:
    """构建Dify配置 - 私有辅助函数"""
    dify_config = {}
    for group in groups:
        if group.enabled:
            config_key = f"{group.name.lower()}_tools"
            
            # 获取完整的API密钥（需要重新从服务获取）
            # 注意：这里需要特殊处理，因为group.api_key_preview是脱敏的
            # 在实际实现中，应该有专门的方法来获取用于配置的API密钥
            
            dify_config[config_key] = {
                "transport": "sse+jsonrpc",
                "url": "http://127.0.0.1:8000/api/v1/mcp/jsonrpc",
                "headers": {},
                "note": "无需在此处配置密钥，Dify 会在 initialize 时弹窗授权，换取 sessionToken",
                "group_info": {
                    "name": group.name,
                    "description": group.description,
                    "user_tier_access": group.user_tier_access,
                    "allowed_roles": group.allowed_roles
                }
            }
    
    return dify_config 