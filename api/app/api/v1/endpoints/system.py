from typing import Any, List, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api import deps
from app.services import system_service
from app.schemas.system import (
    SystemSettingsResponse, 
    SystemSettingsUpdate,
    AIModelConfigCreate,
    AIModelConfigUpdate,
    AIModelConfigResponse,
    AIModelConfigListResponse
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


@router.get("/ai-models", response_model=AIModelConfigListResponse, status_code=status.HTTP_200_OK)
def get_ai_models(
    *,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_admin),
) -> AIModelConfigListResponse:
    """
    获取所有AI模型配置
    """
    return system_service.get_ai_model_configs(db)


@router.post("/ai-models", response_model=AIModelConfigResponse, status_code=status.HTTP_201_CREATED)
def create_ai_model(
    *,
    db: Session = Depends(deps.get_db),
    model_create: AIModelConfigCreate,
    current_user = Depends(deps.get_current_admin),
) -> AIModelConfigResponse:
    """
    创建AI模型配置
    """
    try:
        # 创建AI模型配置
        created_model_data = system_service.create_ai_model_config(db, model_create)
        
        # 通知AI服务配置已更新
        _notify_ai_service_config_change()
        
        # The service returns AIModelConfig, we need to wrap it in AIModelConfigResponse
        return AIModelConfigResponse(success=True, data=created_model_data, message="创建AI模型配置成功")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/ai-models/{model_name}", response_model=AIModelConfigResponse, status_code=status.HTTP_200_OK)
def update_ai_model(
    *,
    db: Session = Depends(deps.get_db),
    model_name: str,
    model_update: AIModelConfigUpdate,
    current_user = Depends(deps.get_current_admin),
) -> AIModelConfigResponse:
    """
    更新AI模型配置
    """
    # 更新AI模型配置
    updated_model_data = system_service.update_ai_model_config(db, model_name, model_update)
    
    if not updated_model_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到名为 '{model_name}' 的AI模型配置"
        )
    
    # 通知AI服务配置已更新
    _notify_ai_service_config_change()
    
    # The service returns AIModelConfig, we need to wrap it in AIModelConfigResponse
    return AIModelConfigResponse(success=True, data=updated_model_data, message="更新AI模型配置成功")


@router.delete("/ai-models/{model_name}", status_code=status.HTTP_200_OK)
def delete_ai_model(
    *,
    db: Session = Depends(deps.get_db),
    model_name: str,
    current_user = Depends(deps.get_current_admin),
) -> Dict[str, Any]:
    """
    删除AI模型配置
    """
    # 删除AI模型配置
    success = system_service.delete_ai_model_config(db, model_name)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到名为 '{model_name}' 的AI模型配置"
        )
    
    # 通知AI服务配置已更新
    _notify_ai_service_config_change()
    
    return {"success": True, "message": "删除AI模型配置成功"}


@router.post("/ai-models/{model_name}/toggle", response_model=AIModelConfigResponse, status_code=status.HTTP_200_OK)
def toggle_ai_model_status(
    *,
    db: Session = Depends(deps.get_db),
    model_name: str,
    current_user = Depends(deps.get_current_admin),
) -> AIModelConfigResponse:
    """
    切换AI模型启用状态
    """
    # 切换AI模型启用状态
    # The service system_service.toggle_ai_model_status already returns AIModelConfigResponse
    toggle_response = system_service.toggle_ai_model_status(db, model_name)
    
    if not toggle_response or not toggle_response.success or not toggle_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到名为 '{model_name}' 的AI模型配置或切换失败"
        )
    
    # 通知AI服务配置已更新
    _notify_ai_service_config_change()
    
    return toggle_response


# 已移除的Dify管理端点 - 现在使用 /api/v1/ai-apps 端点


def _notify_ai_service_config_change():
    """通知AI服务配置已更改"""
    try:
        # 清除AI服务的全局实例，强制重新加载配置
        from app.services.ai.ai_service import _ai_service_instance
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