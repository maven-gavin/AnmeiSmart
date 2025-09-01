"""
Agent配置管理API端点
支持动态配置Agent应用，无需重启服务
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.common.deps import get_db, get_current_admin
from app.ai.schemas.ai import (
    AgentConfigCreate, AgentConfigUpdate, AgentConfigInfo, 
    AgentConfigResponse, AgentConfigListResponse
)
from app.ai.application.agent_config_service import (
    create_agent_config, get_agent_configs, get_agent_config,
    update_agent_config, delete_agent_config, test_agent_connection,
    reload_ai_gateway_with_new_config
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/configs", response_model=AgentConfigListResponse)
def get_agent_config_list(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """获取Agent配置列表"""
    try:
        configs = get_agent_configs(db)
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
    current_user = Depends(get_current_admin)
):
    """获取Agent配置详情"""
    try:
        config = get_agent_config(db, config_id)
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
    current_user = Depends(get_current_admin)
):
    """创建Agent配置"""
    try:
        # 创建配置
        new_config = create_agent_config(db, config_data)
        
        # 动态重载AI Gateway配置
        try:
            reload_ai_gateway_with_new_config()
        except Exception as reload_error:
            # 配置已创建，但重载失败，记录警告
            print(f"Warning: AI Gateway重载失败: {reload_error}")
        
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
    current_user = Depends(get_current_admin)
):
    """更新Agent配置"""
    try:
        # 检查配置是否存在
        existing_config = get_agent_config(db, config_id)
        if not existing_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent配置不存在"
            )
        
        # 更新配置
        updated_config = update_agent_config(db, config_id, config_data)
        
        # 动态重载AI Gateway配置
        try:
            reload_ai_gateway_with_new_config()
        except Exception as reload_error:
            print(f"Warning: AI Gateway重载失败: {reload_error}")
        
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
    current_user = Depends(get_current_admin)
):
    """删除Agent配置"""
    try:
        # 检查配置是否存在
        existing_config = get_agent_config(db, config_id)
        if not existing_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent配置不存在"
            )
        
        # 删除配置
        delete_agent_config(db, config_id)
        
        # 动态重载AI Gateway配置
        try:
            reload_ai_gateway_with_new_config()
        except Exception as reload_error:
            print(f"Warning: AI Gateway重载失败: {reload_error}")
        
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
    current_user = Depends(get_current_admin)
):
    """测试Agent连接"""
    try:
        result = test_agent_connection(config, db)
        
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
    current_user = Depends(get_current_admin)
):
    """手动重载AI Gateway配置"""
    try:
        reload_ai_gateway_with_new_config()
        return {
            "success": True,
            "message": "AI Gateway配置重载成功"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI Gateway配置重载失败: {str(e)}"
        ) 