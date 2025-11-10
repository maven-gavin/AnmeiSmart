from typing import Dict, Any
from app.system.domain.entities.system_settings import SystemSettingsEntity
from app.system.schemas.system import SystemSettings as SystemSettingsSchema, SystemSettingsUpdate


class SystemSettingsConverter:
    """系统设置数据转换器"""
    
    @staticmethod
    def to_response(settings: SystemSettingsEntity) -> SystemSettingsSchema:
        """转换领域实体为API响应Schema"""
        return SystemSettingsSchema(
            siteName=settings.siteConfig.site_name,
            logoUrl=settings.siteConfig.logo_url,
            defaultModelId=settings.aiModelConfig.default_model_id,
            maintenanceMode=settings.maintenanceMode.value,
            userRegistrationEnabled=settings.userRegistrationConfig.enabled
        )
    
    @staticmethod
    def from_update_request(request: SystemSettingsUpdate) -> Dict[str, Any]:
        """从更新请求转换为领域对象参数"""
        update_data = {}
        
        if request.siteName is not None:
            update_data['siteName'] = request.siteName
        
        if request.logoUrl is not None:
            update_data['logoUrl'] = request.logoUrl
        
        if request.defaultModelId is not None:
            update_data['defaultModelId'] = request.defaultModelId
        
        if request.maintenanceMode is not None:
            update_data['maintenanceMode'] = request.maintenanceMode
        
        if request.userRegistrationEnabled is not None:
            update_data['userRegistrationEnabled'] = request.userRegistrationEnabled
        
        return update_data
    
    @staticmethod
    def from_model(model) -> SystemSettingsEntity:
        """从ORM模型转换为领域实体"""
        # 延迟导入避免循环依赖
        from app.system.domain.value_objects.system_config import (
            SiteConfiguration, 
            AIModelConfig, 
            MaintenanceMode, 
            UserRegistrationConfig
        )
        
        return SystemSettingsEntity(
            id=model.id,
            siteConfig=SiteConfiguration(
                site_name=model.site_name,
                logo_url=model.logo_url
            ),
            aiModelConfig=AIModelConfig(
                default_model_id=model.default_model_id
            ),
            maintenanceMode=MaintenanceMode(model.maintenance_mode),
            userRegistrationConfig=UserRegistrationConfig(
                enabled=model.user_registration_enabled
            ),
            createdAt=model.created_at,
            updatedAt=model.updated_at
        )
    
    @staticmethod
    def to_model_dict(settings: SystemSettingsEntity) -> Dict[str, Any]:
        """转换领域实体为ORM模型字典"""
        return {
            "id": settings.id,
            "site_name": settings.siteConfig.site_name,
            "logo_url": settings.siteConfig.logo_url,
            "default_model_id": settings.aiModelConfig.default_model_id,
            "maintenance_mode": settings.maintenanceMode.value,
            "user_registration_enabled": settings.userRegistrationConfig.enabled,
            "created_at": settings.createdAt,
            "updated_at": settings.updatedAt
        }
