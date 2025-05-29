from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api import deps
from app.services import system_service as crud_system
from app.schemas.system import (
    SystemSettingsResponse, 
    SystemSettingsUpdate,
    AIModelConfigCreate,
    AIModelConfigUpdate,
    AIModelConfigResponse,
    AIModelConfigListResponse
)

router = APIRouter()


@router.get("/settings", response_model=SystemSettingsResponse, status_code=status.HTTP_200_OK)
def get_system_settings(
    *,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_admin),
) -> Any:
    """
    获取系统设置
    """
    # 获取或创建系统设置
    system_settings = crud_system.get_or_create_system_settings(db)
    
    # 获取所有AI模型配置
    ai_models = crud_system.get_ai_model_configs(db)
    
    # 构建响应数据
    response_data = {
        "siteName": system_settings.siteName,
        "logoUrl": system_settings.logoUrl,
        "defaultModelId": system_settings.defaultModelId,
        "maintenanceMode": system_settings.maintenanceMode,
        "userRegistrationEnabled": system_settings.userRegistrationEnabled,
        "aiModels": [
            {
                "modelName": model.modelName,
                "apiKey": "••••••••••••••••••••",  # 不返回实际API密钥
                "baseUrl": model.baseUrl,
                "maxTokens": model.maxTokens,
                "temperature": model.temperature,
                "enabled": model.enabled,
                "provider": model.provider,
                "appId": model.appId
            }
            for model in ai_models
        ]
    }
    
    return {"success": True, "data": response_data, "message": "获取系统设置成功"}


@router.put("/settings", response_model=SystemSettingsResponse, status_code=status.HTTP_200_OK)
def update_system_settings(
    *,
    db: Session = Depends(deps.get_db),
    settings_update: SystemSettingsUpdate,
    current_user = Depends(deps.get_current_admin),
) -> Any:
    """
    更新系统设置
    """
    # 更新系统设置
    updated_settings = crud_system.update_system_settings(db, settings_update)
    
    # 获取所有AI模型配置
    ai_models = crud_system.get_ai_model_configs(db)
    
    # 构建响应数据
    response_data = {
        "siteName": updated_settings.siteName,
        "logoUrl": updated_settings.logoUrl,
        "defaultModelId": updated_settings.defaultModelId,
        "maintenanceMode": updated_settings.maintenanceMode,
        "userRegistrationEnabled": updated_settings.userRegistrationEnabled,
        "aiModels": [
            {
                "modelName": model.modelName,
                "apiKey": "••••••••••••••••••••",  # 不返回实际API密钥
                "baseUrl": model.baseUrl,
                "maxTokens": model.maxTokens,
                "temperature": model.temperature,
                "enabled": model.enabled
            }
            for model in ai_models
        ]
    }
    
    return {"success": True, "data": response_data, "message": "更新系统设置成功"}


@router.get("/ai-models", response_model=AIModelConfigListResponse, status_code=status.HTTP_200_OK)
def get_ai_models(
    *,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_admin),
) -> Any:
    """
    获取所有AI模型配置
    """
    # 获取所有AI模型配置
    ai_models = crud_system.get_ai_model_configs(db)
    
    # 构建响应数据
    response_data = [
        {
            "modelName": model.modelName,
            "apiKey": "••••••••••••••••••••",  # 不返回实际API密钥
            "baseUrl": model.baseUrl,
            "maxTokens": model.maxTokens,
            "temperature": model.temperature,
            "enabled": model.enabled
        }
        for model in ai_models
    ]
    
    return {"success": True, "data": response_data, "message": "获取AI模型配置成功"}


@router.post("/ai-models", response_model=AIModelConfigResponse, status_code=status.HTTP_201_CREATED)
def create_ai_model(
    *,
    db: Session = Depends(deps.get_db),
    model_create: AIModelConfigCreate,
    current_user = Depends(deps.get_current_admin),
) -> Any:
    """
    创建AI模型配置
    """
    try:
        # 创建AI模型配置
        created_model = crud_system.create_ai_model_config(db, model_create)
        
        # 构建响应数据
        response_data = {
            "modelName": created_model.modelName,
            "apiKey": "••••••••••••••••••••",  # 不返回实际API密钥
            "baseUrl": created_model.baseUrl,
            "maxTokens": created_model.maxTokens,
            "temperature": created_model.temperature,
            "enabled": created_model.enabled
        }
        
        return {"success": True, "data": response_data, "message": "创建AI模型配置成功"}
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
) -> Any:
    """
    更新AI模型配置
    """
    # 更新AI模型配置
    updated_model = crud_system.update_ai_model_config(db, model_name, model_update)
    
    if not updated_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到名为 '{model_name}' 的AI模型配置"
        )
    
    # 构建响应数据
    response_data = {
        "modelName": updated_model.modelName,
        "apiKey": "••••••••••••••••••••",  # 不返回实际API密钥
        "baseUrl": updated_model.baseUrl,
        "maxTokens": updated_model.maxTokens,
        "temperature": updated_model.temperature,
        "enabled": updated_model.enabled
    }
    
    return {"success": True, "data": response_data, "message": "更新AI模型配置成功"}


@router.delete("/ai-models/{model_name}", status_code=status.HTTP_200_OK)
def delete_ai_model(
    *,
    db: Session = Depends(deps.get_db),
    model_name: str,
    current_user = Depends(deps.get_current_admin),
) -> Any:
    """
    删除AI模型配置
    """
    # 删除AI模型配置
    success = crud_system.delete_ai_model_config(db, model_name)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到名为 '{model_name}' 的AI模型配置"
        )
    
    return {"success": True, "message": "删除AI模型配置成功"}


@router.post("/ai-models/{model_name}/toggle", response_model=AIModelConfigResponse, status_code=status.HTTP_200_OK)
def toggle_ai_model_status(
    *,
    db: Session = Depends(deps.get_db),
    model_name: str,
    current_user = Depends(deps.get_current_admin),
) -> Any:
    """
    切换AI模型启用状态
    """
    # 切换AI模型启用状态
    updated_model = crud_system.toggle_ai_model_status(db, model_name)
    
    if not updated_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到名为 '{model_name}' 的AI模型配置"
        )
    
    # 构建响应数据
    response_data = {
        "modelName": updated_model.modelName,
        "apiKey": "••••••••••••••••••••",  # 不返回实际API密钥
        "baseUrl": updated_model.baseUrl,
        "maxTokens": updated_model.maxTokens,
        "temperature": updated_model.temperature,
        "enabled": updated_model.enabled
    }
    
    return {"success": True, "data": response_data, "message": f"AI模型 '{model_name}' 已{('启用' if updated_model.enabled else '停用')}"} 