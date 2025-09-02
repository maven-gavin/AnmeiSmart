"""
客户领域模块
"""

from .entities.customer import Customer, CustomerProfile
from .value_objects.customer_status import CustomerStatus, CustomerPriority
from .customer_domain_service import CustomerDomainService

__all__ = [
    "Customer",
    "CustomerProfile", 
    "CustomerStatus",
    "CustomerPriority",
    "CustomerDomainService"
]
