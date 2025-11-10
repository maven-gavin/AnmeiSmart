from typing import Optional
from app.system.domain.entities.system_settings import SystemSettingsEntity
from app.system.domain.value_objects.system_config import MaintenanceMode


class SystemDomainService:
    """系统设置领域服务"""
    
    def __init__(self):
        pass
    
    def validate_system_settings(self, settings: SystemSettingsEntity) -> bool:
        """验证系统设置的有效性"""
        if not settings.siteConfig.site_name.strip():
            return False
        
        if settings.maintenanceMode == MaintenanceMode.ENABLED:
            # 维护模式下，某些功能可能受限
            pass
        
        return True
    
    def can_enable_maintenance_mode(self, current_settings: SystemSettingsEntity) -> bool:
        """检查是否可以启用维护模式"""
        # 这里可以添加业务规则，比如检查是否有活跃的会话等
        return True
    
    def can_disable_maintenance_mode(self, current_settings: SystemSettingsEntity) -> bool:
        """检查是否可以禁用维护模式"""
        # 这里可以添加业务规则
        return True
    
    def validate_ai_model_config(self, model_id: Optional[str]) -> bool:
        """验证AI模型配置"""
        if model_id is not None and not model_id.strip():
            return False
        return True
    
    def get_system_health_status(self, settings: SystemSettingsEntity) -> str:
        """获取系统健康状态"""
        if settings.isMaintenanceMode():
            return "maintenance"
        return "healthy"
