"""
Contact领域依赖注入配置
遵循DDD分层架构的依赖注入最佳实践
"""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.infrastructure.db.base import get_db
from app.contacts.application.contact_application_service import ContactApplicationService
from app.contacts.infrastructure.contact_repository import ContactRepository
from app.contacts.domain.contact_domain_service import ContactDomainService
from app.contacts.integration.chat_integration_service import ChatIntegrationService


def get_contact_repository(db: Session = Depends(get_db)) -> ContactRepository:
    """获取联系人仓储实例"""
    return ContactRepository(db)


def get_contact_domain_service(
    contact_repository: ContactRepository = Depends(get_contact_repository)
) -> ContactDomainService:
    """获取联系人领域服务实例"""
    return ContactDomainService(contact_repository)


def get_contact_application_service(
    contact_repository: ContactRepository = Depends(get_contact_repository),
    contact_domain_service: ContactDomainService = Depends(get_contact_domain_service)
) -> ContactApplicationService:
    """获取联系人应用服务实例"""
    return ContactApplicationService(
        contact_repository=contact_repository,
        contact_domain_service=contact_domain_service
    )


def get_chat_integration_service(
    contact_app_service: ContactApplicationService = Depends(get_contact_application_service)
) -> ChatIntegrationService:
    """获取Chat集成服务实例"""
    # 延迟导入避免循环依赖
    from app.chat.deps.chat import get_chat_application_service
    from app.chat.application.chat_application_service import ChatApplicationService
    
    # 这里需要获取Chat应用服务实例
    # 暂时返回None，实际实现时需要正确注入Chat应用服务
    return ChatIntegrationService(
        contact_app_service=contact_app_service,
        chat_app_service=None  # 需要正确注入
    )
