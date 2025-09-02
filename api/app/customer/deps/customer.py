"""
客户依赖注入配置
"""
from typing import Optional
from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.deps import get_db
from app.customer.application.customer_application_service import CustomerApplicationService
from app.customer.domain.customer_domain_service import CustomerDomainService
from app.customer.infrastructure.repositories.customer_repository import CustomerRepository
from app.customer.infrastructure.repositories.customer_profile_repository import CustomerProfileRepository


def get_customer_repository(db: Session = Depends(get_db)) -> CustomerRepository:
    """获取客户仓储实例"""
    return CustomerRepository(db)


def get_customer_profile_repository(db: Session = Depends(get_db)) -> CustomerProfileRepository:
    """获取客户档案仓储实例"""
    return CustomerProfileRepository(db)


def get_customer_domain_service() -> CustomerDomainService:
    """获取客户领域服务实例"""
    return CustomerDomainService()


def get_customer_application_service(
    customer_repository: CustomerRepository = Depends(get_customer_repository),
    customer_profile_repository: CustomerProfileRepository = Depends(get_customer_profile_repository),
    customer_domain_service: CustomerDomainService = Depends(get_customer_domain_service)
) -> CustomerApplicationService:
    """获取客户应用服务实例"""
    return CustomerApplicationService(
        customer_repository=customer_repository,
        customer_profile_repository=customer_profile_repository,
        customer_domain_service=customer_domain_service
    )
