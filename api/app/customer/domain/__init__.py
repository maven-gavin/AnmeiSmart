"""
客户领域模块
"""

from .entities.customer import CustomerEntity, CustomerProfileEntity
from .value_objects.customer_status import CustomerStatus, CustomerPriority
from .customer_domain_service import CustomerDomainService

__all__ = [
    "CustomerEntity",
    "CustomerProfileEntity", 
    "CustomerStatus",
    "CustomerPriority",
    "CustomerDomainService"
]
