"""
数字人管理API端点
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.common.deps import get_db
from ..deps.digital_humans import get_digital_human_service
from app.identity_access.deps import get_current_user
from app.identity_access.models.user import User
from ..schemas.digital_human import (
    DigitalHumanResponse,
    CreateDigitalHumanRequest,
    UpdateDigitalHumanRequest,
    AddAgentConfigRequest,
    DigitalHumanAgentConfigInfo,
    UpdateAgentConfigRequest,
)
from ..deps.digital_humans import get_digital_human_service
from ..services.digital_human_service import DigitalHumanService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def get_digital_humans(
    current_user: User = Depends(get_current_user),
    service: DigitalHumanService = Depends(get_digital_human_service)
):
    """获取当前用户的数字人列表"""
    try:
        digital_humans = service.get_user_digital_humans(current_user.id)
        
        return {
            "success": True,
            "data": digital_humans,
            "message": "获取数字人列表成功"
        }
        
    except Exception as e:
        logger.error(f"获取数字人列表失败: {e}")
        return {
            "success": False,
            "data": [],
            "message": f"获取数字人列表失败: {str(e)}"
        }


@router.get("/{digital_human_id}", response_model=DigitalHumanResponse)
async def get_digital_human(
    digital_human_id: str,
    current_user: User = Depends(get_current_user),
    service: DigitalHumanService = Depends(get_digital_human_service)
):
    """获取数字人详情"""
    try:
        digital_human = service.get_digital_human_by_id(digital_human_id, current_user.id)
        
        if not digital_human:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="数字人不存在或无权限访问"
            )
        
        return digital_human
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取数字人详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取数字人详情失败"
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_digital_human(
    data: CreateDigitalHumanRequest,
    current_user: User = Depends(get_current_user),
    service: DigitalHumanService = Depends(get_digital_human_service)
):
    """创建数字人"""
    try:
        digital_human = service.create_digital_human(current_user.id, data)
        
        return {
            "success": True,
            "data": digital_human,
            "message": "创建数字人成功"
        }
        
    except Exception as e:
        logger.error(f"创建数字人失败: {e}")
        return {
            "success": False,
            "data": None,
            "message": f"创建数字人失败: {str(e)}"
        }


@router.put("/{digital_human_id}", response_model=DigitalHumanResponse)
async def update_digital_human(
    digital_human_id: str,
    data: UpdateDigitalHumanRequest,
    current_user: User = Depends(get_current_user),
    service: DigitalHumanService = Depends(get_digital_human_service)
):
    """更新数字人信息"""
    try:
        digital_human = service.update_digital_human(digital_human_id, current_user.id, data)
        
        if not digital_human:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="数字人不存在或无权限修改"
            )
        
        return digital_human
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新数字人失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新数字人失败: {str(e)}"
        )


@router.delete("/{digital_human_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_digital_human(
    digital_human_id: str,
    current_user: User = Depends(get_current_user),
    service: DigitalHumanService = Depends(get_digital_human_service)
):
    """删除数字人（系统创建的不可删除）"""
    try:
        success = service.delete_digital_human(digital_human_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="数字人不存在、无权限删除或为系统创建"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除数字人失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除数字人失败: {str(e)}"
        )


@router.get("/{digital_human_id}/agents", response_model=List[DigitalHumanAgentConfigInfo])
async def get_digital_human_agents(
    digital_human_id: str,
    current_user: User = Depends(get_current_user),
    service: DigitalHumanService = Depends(get_digital_human_service)
):
    """获取数字人的智能体配置列表"""
    try:
        agent_configs = service.get_digital_human_agents(digital_human_id, current_user.id)
        
        return agent_configs
        
    except Exception as e:
        logger.error(f"获取数字人智能体配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取智能体配置失败"
        )


@router.post("/{digital_human_id}/agents", response_model=DigitalHumanAgentConfigInfo, status_code=status.HTTP_201_CREATED)
async def add_agent_to_digital_human(
    digital_human_id: str,
    data: AddAgentConfigRequest,
    current_user: User = Depends(get_current_user),
    service: DigitalHumanService = Depends(get_digital_human_service)
):
    """为数字人添加智能体配置"""
    try:
        agent_config = service.add_agent_to_digital_human(digital_human_id, current_user.id, data)
        
        return agent_config
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"添加智能体配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加智能体配置失败: {str(e)}"
        )


@router.delete("/{digital_human_id}/agents/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_agent_from_digital_human(
    digital_human_id: str,
    config_id: str,
    current_user: User = Depends(get_current_user),
    service: DigitalHumanService = Depends(get_digital_human_service)
):
    """从数字人移除智能体配置"""
    try:
        success = service.remove_agent_from_digital_human(digital_human_id, config_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="智能体配置不存在或无权限删除"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"移除智能体配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"移除智能体配置失败: {str(e)}"
        )


@router.put("/{digital_human_id}/agents/{config_id}", response_model=DigitalHumanAgentConfigInfo)
async def update_digital_human_agent(
    digital_human_id: str,
    config_id: str,
    data: UpdateAgentConfigRequest,
    current_user: User = Depends(get_current_user),
    service: DigitalHumanService = Depends(get_digital_human_service),
):
    """更新数字人的智能体配置"""
    try:
        updated_config = service.update_digital_human_agent(
            digital_human_id=digital_human_id,
            config_id=config_id,
            user_id=current_user.id,
            data=data,
        )

        if not updated_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="智能体配置不存在或无权限修改",
            )

        return updated_config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新数字人智能体配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新智能体配置失败",
        )
