"""
系统设置领域层

包含：
- 聚合根：SystemSettings
- 值对象：SiteConfiguration, UserRegistrationConfig, AIModelConfig等
- 领域服务：SystemDomainService
"""

from app.system.domain.entities.system_settings import SystemSettings
from app.system.domain.value_objects.system_config import (
    SystemStatus,
    MaintenanceMode,
    SiteConfiguration,
    UserRegistrationConfig,
    AIModelConfig
)
from app.system.domain.system_domain_service import SystemDomainService

__all__ = [
    "SystemSettings",
    "SystemStatus",
    "MaintenanceMode", 
    "SiteConfiguration",
    "UserRegistrationConfig",
    "AIModelConfig",
    "SystemDomainService",
]
