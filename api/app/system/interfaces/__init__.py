"""
系统设置接口定义

包含：
- 仓储接口：ISystemSettingsRepository
- 领域服务接口：ISystemDomainService
- 应用服务接口：ISystemApplicationService
"""

from app.system.interfaces.repository_interfaces import ISystemSettingsRepository
from app.system.interfaces.domain_service_interfaces import ISystemDomainService
from app.system.interfaces.application_service_interfaces import ISystemApplicationService

__all__ = [
    "ISystemSettingsRepository",
    "ISystemDomainService",
    "ISystemApplicationService",
]
