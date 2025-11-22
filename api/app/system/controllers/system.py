"""
系统模块API控制器 - 管理系统设置和健康检查
"""
from fastapi import APIRouter, Depends, status, HTTPException
from app.system.deps.system import get_system_service
from app.system.services.system_service import SystemService
from app.system.schemas.system import (
    SystemSettingsResponse, 
    SystemSettingsUpdate,
)
from app.identity_access.deps import get_current_admin
from app.core.api import BusinessException, ErrorCode
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/settings", response_model=SystemSettingsResponse, status_code=status.HTTP_200_OK)
async def get_system_settings(
    system_service: SystemService = Depends(get_system_service),
) -> SystemSettingsResponse:
    """获取系统设置"""
    try:
        return system_service.get_system_settings()
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取系统设置失败: {e}")
        raise HTTPException(status_code=500, detail="系统设置获取失败")


@router.put("/settings", response_model=SystemSettingsResponse, status_code=status.HTTP_200_OK)
async def update_system_settings(
    settings_update: SystemSettingsUpdate,
    system_service: SystemService = Depends(get_system_service),
    current_user = Depends(get_current_admin),
) -> SystemSettingsResponse:
    """更新系统设置"""
    try:
        return system_service.update_system_settings(settings_update)
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新系统设置失败: {e}")
        raise HTTPException(status_code=500, detail="系统设置更新失败")


@router.get("/health", status_code=status.HTTP_200_OK)
async def get_system_health(
    system_service: SystemService = Depends(get_system_service),
):
    """获取系统健康状态"""
    try:
        return system_service.get_system_health()
    except Exception as e:
        logger.error(f"获取系统健康状态失败: {e}")
        return {"status": "error", "message": "系统健康检查失败"} 