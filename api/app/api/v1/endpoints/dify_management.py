"""
Dify管理API端点
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.db.models.user import User
from app.services.ai.dify_connection_service import DifyConnectionService
from app.schemas.system import DifyConnectionCreate, DifyConnectionInfo, ConfigureAppRequest, AgentTypeInfo

router = APIRouter()

@router.post("/connections", response_model=Dict[str, Any])
async def create_dify_connection(
    connection_data: DifyConnectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建Dify连接"""
    try:
        service = DifyConnectionService(db)
        connection = service.create_connection(
            name=connection_data.name,
            api_base_url=connection_data.api_base_url,
            api_key=connection_data.api_key,
            description=connection_data.description,
            is_default=connection_data.is_default
        )
        
        return {
            "success": True,
            "message": "Dify连接创建成功",
            "connection_id": connection.id
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/connections")
async def get_dify_connections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有Dify连接"""
    service = DifyConnectionService(db)
    connections = service.get_connections()
    
    return {
        "connections": [
            DifyConnectionInfo.from_model(conn)
            for conn in connections
        ]
    }

@router.post("/connections/{connection_id}/test")
async def test_dify_connection(
    connection_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """测试Dify连接"""
    service = DifyConnectionService(db)
    result = await service.test_connection(connection_id)
    return result

@router.post("/connections/{connection_id}/sync")
async def sync_dify_apps(
    connection_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """同步Dify应用"""
    service = DifyConnectionService(db)
    result = await service.sync_apps(connection_id)
    return result

@router.get("/connections/{connection_id}/apps")
async def get_dify_apps(
    connection_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取Dify应用列表"""
    service = DifyConnectionService(db)
    apps = await service.get_available_apps(connection_id)
    return {"apps": apps}

@router.post("/apps/configure")
async def configure_dify_app(
    config_data: ConfigureAppRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """配置Dify应用到特定功能"""
    try:
        service = DifyConnectionService(db)
        config = service.configure_app_to_agent_type(
            connection_id=config_data.connection_id,
            app_id=config_data.app_id,
            app_name=config_data.app_name,
            app_mode=config_data.app_mode,
            agent_type=config_data.agent_type,
            description=config_data.description,
            is_default_for_type=config_data.is_default_for_type
        )
        
        return {
            "success": True,
            "message": "应用配置成功",
            "config_id": config.id
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/agent-types", response_model=List[AgentTypeInfo])
async def get_agent_types():
    """获取可用的Agent类型"""
    return [
        AgentTypeInfo(
            value="general_chat", 
            label="通用聊天", 
            description="处理一般性对话和问答"
        ),
        AgentTypeInfo(
            value="beauty_plan", 
            label="医美方案生成", 
            description="为客户制定个性化医美方案"
        ),
        AgentTypeInfo(
            value="consultation", 
            label="咨询总结", 
            description="总结和分析咨询内容"
        ),
        AgentTypeInfo(
            value="customer_service", 
            label="客服支持", 
            description="处理客户服务相关问题"
        ),
        AgentTypeInfo(
            value="medical_advice", 
            label="医疗建议", 
            description="提供专业的医疗建议"
        )
    ]

@router.delete("/connections/{connection_id}")
async def delete_dify_connection(
    connection_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除Dify连接"""
    service = DifyConnectionService(db)
    success = service.delete_connection(connection_id)
    
    if success:
        return {"success": True, "message": "连接删除成功"}
    else:
        raise HTTPException(status_code=404, detail="连接不存在")

@router.put("/connections/{connection_id}/set-default")
async def set_default_connection(
    connection_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """设置默认连接"""
    service = DifyConnectionService(db)
    success = service.set_default_connection(connection_id)
    
    if success:
        return {"success": True, "message": "默认连接设置成功"}
    else:
        raise HTTPException(status_code=404, detail="连接不存在") 