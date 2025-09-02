from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.common.infrastructure.db.base import get_db

from app.system.deps.system import get_system_application_service
from app.system.interfaces.application_service_interfaces import ISystemApplicationService
from app.system.schemas.system import (
    SystemSettingsResponse, 
    SystemSettingsUpdate,
)
from app.identity_access.deps import get_current_admin
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/settings", response_model=SystemSettingsResponse, status_code=status.HTTP_200_OK)
async def get_system_settings(
    *,
    system_app_service: ISystemApplicationService = Depends(get_system_application_service),
) -> SystemSettingsResponse:
    """
    获取系统设置 - 表现层只负责请求路由和响应格式化
    """
    try:
        return await system_app_service.get_system_settings()
        
    except ValueError as e:
        # 业务逻辑错误 - 400 Bad Request
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        # 系统错误 - 500 Internal Server Error
        logger.error(f"获取系统设置失败: {e}")
        raise HTTPException(status_code=500, detail="系统设置获取失败")
    except Exception as e:
        # 未知错误 - 500 Internal Server Error
        logger.error(f"获取系统设置时发生未知错误: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.put("/settings", response_model=SystemSettingsResponse, status_code=status.HTTP_200_OK)
async def update_system_settings(
    *,
    settings_update: SystemSettingsUpdate,
    system_app_service: ISystemApplicationService = Depends(get_system_application_service),
    current_user = Depends(get_current_admin),
) -> SystemSettingsResponse:
    """
    更新系统设置 - 表现层只负责请求路由和响应格式化
    """
    try:
        return await system_app_service.update_system_settings(settings_update)
        
    except ValueError as e:
        # 业务逻辑错误 - 400 Bad Request
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        # 系统错误 - 500 Internal Server Error
        logger.error(f"更新系统设置失败: {e}")
        raise HTTPException(status_code=500, detail="系统设置更新失败")
    except Exception as e:
        # 未知错误 - 500 Internal Server Error
        logger.error(f"更新系统设置时发生未知错误: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.get("/health", status_code=status.HTTP_200_OK)
async def get_system_health(
    *,
    system_app_service: ISystemApplicationService = Depends(get_system_application_service),
):
    """
    获取系统健康状态 - 表现层只负责请求路由和响应格式化
    """
    try:
        return await system_app_service.get_system_health()
        
    except Exception as e:
        # 健康检查失败 - 500 Internal Server Error
        logger.error(f"获取系统健康状态失败: {e}")
        return {"status": "error", "message": "系统健康检查失败"} 