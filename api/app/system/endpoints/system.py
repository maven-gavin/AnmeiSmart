from typing import Any, List, Dict, Optional, Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.common.infrastructure.db.base import deps
from app.system.application import system_service
from app.system.schemas.system import (
    SystemSettingsResponse, 
    SystemSettingsUpdate,

)
# 移除了Dify相关导入，现在使用独立的AI应用管理模块

router = APIRouter()


@router.get("/settings", response_model=SystemSettingsResponse, status_code=status.HTTP_200_OK)
def get_system_settings(
    *,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_admin),
) -> SystemSettingsResponse:
    """
    获取系统设置
    """
    # 直接调用service层方法，该方法已返回所需格式的响应
    return system_service.get_system_settings(db)


@router.put("/settings", response_model=SystemSettingsResponse, status_code=status.HTTP_200_OK)
def update_system_settings(
    *,
    db: Session = Depends(deps.get_db),
    settings_update: SystemSettingsUpdate,
    current_user = Depends(deps.get_current_admin),
) -> SystemSettingsResponse:
    """
    更新系统设置
    """
    # 直接调用service层方法，该方法已返回所需格式的响应
    return system_service.update_system_settings(db, settings_update)





# 已移除的Dify管理端点 - 现在使用 /api/v1/ai-apps 端点


def _notify_ai_service_config_change():
    """通知AI服务配置已更改"""
    try:
        # 清除AI服务的全局实例，强制重新加载配置
        from app.ai.application import _ai_service_instance
        if _ai_service_instance:
            _ai_service_instance.reload_configurations()
        
        # 可以在这里添加其他通知机制，如发布事件等
        import logging
        logger = logging.getLogger(__name__)
        logger.info("AI服务配置变更通知已发送")
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"通知AI服务配置变更失败: {e}") 