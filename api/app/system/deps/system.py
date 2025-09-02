from typing import Optional
from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.infrastructure.db.base import get_db
from app.system.infrastructure.repositories.system_settings_repository import SystemSettingsRepository
from app.system.domain.system_domain_service import SystemDomainService
from app.system.application.system_application_service import SystemApplicationService
from app.system.interfaces.repository_interfaces import ISystemSettingsRepository
from app.system.interfaces.domain_service_interfaces import ISystemDomainService
from app.system.interfaces.application_service_interfaces import ISystemApplicationService


def get_system_settings_repository(db: Session = Depends(get_db)) -> ISystemSettingsRepository:
    """获取系统设置仓储实例"""
    return SystemSettingsRepository(db)


def get_system_domain_service() -> ISystemDomainService:
    """获取系统领域服务实例"""
    return SystemDomainService()


def get_system_application_service(
    system_settings_repository: ISystemSettingsRepository = Depends(get_system_settings_repository),
    system_domain_service: ISystemDomainService = Depends(get_system_domain_service)
) -> ISystemApplicationService:
    """获取系统应用服务实例"""
    return SystemApplicationService(
        system_settings_repository=system_settings_repository,
        system_domain_service=system_domain_service
    )
