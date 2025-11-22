"""
客户依赖注入模块
"""

from .customer import get_customer_service, check_customer_permission

__all__ = [
    "get_customer_service",
    "check_customer_permission"
]
