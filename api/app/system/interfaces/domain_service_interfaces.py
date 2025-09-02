from abc import ABC, abstractmethod
from typing import Optional
from app.system.domain.entities.system_settings import SystemSettings


class ISystemDomainService(ABC):
    """系统设置领域服务接口"""
    
    @abstractmethod
    def validate_system_settings(self, settings: SystemSettings) -> bool:
        """验证系统设置的有效性"""
        pass
    
    @abstractmethod
    def can_enable_maintenance_mode(self, current_settings: SystemSettings) -> bool:
        """检查是否可以启用维护模式"""
        pass
    
    @abstractmethod
    def can_disable_maintenance_mode(self, current_settings: SystemSettings) -> bool:
        """检查是否可以禁用维护模式"""
        pass
    
    @abstractmethod
    def validate_ai_model_config(self, model_id: Optional[str]) -> bool:
        """验证AI模型配置"""
        pass
    
    @abstractmethod
    def get_system_health_status(self, settings: SystemSettings) -> str:
        """获取系统健康状态"""
        pass
