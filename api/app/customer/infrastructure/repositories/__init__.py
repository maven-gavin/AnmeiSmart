"""
客户仓储模块
"""

from .customer_repository import CustomerRepository
from .customer_profile_repository import CustomerProfileRepository

__all__ = [
    "CustomerRepository",
    "CustomerProfileRepository"
]
