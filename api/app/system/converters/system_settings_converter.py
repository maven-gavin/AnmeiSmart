from typing import Optional, Dict, Any
from app.system.domain.entities.system_settings import SystemSettings
from app.system.schemas.system import SystemSettings as SystemSettingsSchema, SystemSettingsUpdate


class SystemSettingsConverter:
    """系统设置数据转换器"""
    
    @staticmethod
    def to_response(settings: SystemSettings) -> SystemSettingsSchema:
        """转换领域实体为API响应Schema"""
        return SystemSettingsSchema(
            siteName=settings.site_config.site_name,
            logoUrl=settings.site_config.logo_url,
            defaultModelId=settings.ai_model_config.default_model_id,
            maintenanceMode=settings.maintenance_mode.value,
            userRegistrationEnabled=settings.user_registration_config.enabled
        )
    
    @staticmethod
    def from_update_request(request: SystemSettingsUpdate) -> Dict[str, Any]:
        """从更新请求转换为领域对象参数"""
        update_data = {}
        
        if request.siteName is not None:
            update_data['site_name'] = request.siteName
        
        if request.logoUrl is not None:
            update_data['logo_url'] = request.logoUrl
        
        if request.defaultModelId is not None:
            update_data['default_model_id'] = request.defaultModelId
        
        if request.maintenanceMode is not None:
            update_data['maintenance_mode'] = request.maintenanceMode
        
        if request.userRegistrationEnabled is not None:
            update_data['user_registration_enabled'] = request.userRegistrationEnabled
        
        return update_data
    
    @staticmethod
    def from_model(model) -> SystemSettings:
        """从ORM模型转换为领域实体"""
        # 延迟导入避免循环依赖
        from app.system.domain.value_objects.system_config import (
            SiteConfiguration, 
            AIModelConfig, 
            MaintenanceMode, 
            UserRegistrationConfig
        )
        
        return SystemSettings(
            id=model.id,
            site_config=SiteConfiguration(
                site_name=model.site_name,
                logo_url=model.logo_url
            ),
            ai_model_config=AIModelConfig(
                default_model_id=model.default_model_id
            ),
            maintenance_mode=MaintenanceMode(model.maintenance_mode),
            user_registration_config=UserRegistrationConfig(
                enabled=model.user_registration_enabled
            ),
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    @staticmethod
    def to_model_dict(settings: SystemSettings) -> Dict[str, Any]:
        """转换领域实体为ORM模型字典"""
        return {
            "id": settings.id,
            "site_name": settings.site_config.site_name,
            "logo_url": settings.site_config.logo_url,
            "default_model_id": settings.ai_model_config.default_model_id,
            "maintenance_mode": settings.maintenance_mode.value,
            "user_registration_enabled": settings.user_registration_config.enabled,
            "created_at": settings.created_at,
            "updated_at": settings.updated_at
        }
