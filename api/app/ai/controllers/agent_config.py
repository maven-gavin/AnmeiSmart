"""
Agent配置管理控制器
支持动态配置Agent应用，无需重启服务
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.common.deps import get_db
from app.identity_access.deps import get_current_admin, get_current_user
from app.ai.schemas.ai import (
    AgentConfigCreate, AgentConfigUpdate, AgentConfigInfo, 
    AgentConfigResponse, AgentConfigListResponse
)
from app.ai.services.agent_config_service import AgentConfigService
from app.ai.deps import get_agent_config_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/configs", response_model=AgentConfigListResponse)
def get_agent_config_list(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    service: AgentConfigService = Depends(get_agent_config_service)
):
    """获取Agent配置列表（所有用户可访问）"""
    try:
        configs = service.get_agent_configs()
        return AgentConfigListResponse(
            success=True,
            data=configs,
            message="获取Agent配置列表成功"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取Agent配置列表失败: {str(e)}"
        )


@router.get("/configs/{config_id}", response_model=AgentConfigResponse)
def get_agent_config_detail(
    config_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    service: AgentConfigService = Depends(get_agent_config_service)
):
    """获取Agent配置详情（所有用户可访问）"""
    try:
        config = service.get_agent_config(config_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent配置不存在"
            )
        
        return AgentConfigResponse(
            success=True,
            data=config,
            message="获取Agent配置详情成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取Agent配置详情失败: {str(e)}"
        )


@router.post("/configs", response_model=AgentConfigResponse)
def create_agent_config_endpoint(
    config_data: AgentConfigCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin),
    service: AgentConfigService = Depends(get_agent_config_service)
):
    """创建Agent配置"""
    try:
        # 创建配置
        new_config = service.create_agent_config(config_data)
        
        # 动态重载AI Gateway配置
        try:
            service.reload_ai_gateway()
        except Exception as reload_error:
            # 配置已创建，但重载失败，记录警告
            logger.warning(f"AI Gateway重载失败: {reload_error}")
        
        return AgentConfigResponse(
            success=True,
            data=new_config,
            message="创建Agent配置成功"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建Agent配置失败: {str(e)}"
        )


@router.put("/configs/{config_id}", response_model=AgentConfigResponse)
def update_agent_config_endpoint(
    config_id: str,
    config_data: AgentConfigUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin),
    service: AgentConfigService = Depends(get_agent_config_service)
):
    """更新Agent配置"""
    try:
        # 检查配置是否存在
        existing_config = service.get_agent_config(config_id)
        if not existing_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent配置不存在"
            )
        
        # 更新配置
        updated_config = service.update_agent_config(config_id, config_data)
        
        # 动态重载AI Gateway配置
        try:
            service.reload_ai_gateway()
        except Exception as reload_error:
            logger.warning(f"AI Gateway重载失败: {reload_error}")
        
        return AgentConfigResponse(
            success=True,
            data=updated_config,
            message="更新Agent配置成功"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新Agent配置失败: {str(e)}"
        )


@router.delete("/configs/{config_id}")
def delete_agent_config_endpoint(
    config_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin),
    service: AgentConfigService = Depends(get_agent_config_service)
):
    """删除Agent配置"""
    try:
        # 检查配置是否存在
        existing_config = service.get_agent_config(config_id)
        if not existing_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent配置不存在"
            )
        
        # 删除配置
        service.delete_agent_config(config_id)
        
        # 动态重载AI Gateway配置
        try:
            service.reload_ai_gateway()
        except Exception as reload_error:
            logger.warning(f"AI Gateway重载失败: {reload_error}")
        
        return {
            "success": True,
            "message": "删除Agent配置成功"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除Agent配置失败: {str(e)}"
        )


@router.post("/test-connection")
def test_agent_connection_endpoint(
    config: AgentConfigInfo,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin),
    service: AgentConfigService = Depends(get_agent_config_service)
):
    """测试Agent连接"""
    try:
        result = service.test_agent_connection(config)
        
        return {
            "success": result["success"],
            "message": result["message"],
            "details": result.get("details", {})
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"连接测试失败: {str(e)}",
            "details": {}
        }


@router.post("/reload-gateway")
def reload_ai_gateway_endpoint(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin),
    service: AgentConfigService = Depends(get_agent_config_service)
):
    """手动重载AI Gateway配置"""
    try:
        service.reload_ai_gateway()
        return {
            "success": True,
            "message": "AI Gateway配置重载成功"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI Gateway配置重载失败: {str(e)}"
        )
