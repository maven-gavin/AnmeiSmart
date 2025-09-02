"""
客户状态和优先级值对象
"""
from enum import Enum


class CustomerStatus(str, Enum):
    """客户状态枚举"""
    ACTIVE = "active"           # 活跃
    INACTIVE = "inactive"       # 非活跃
    SUSPENDED = "suspended"     # 暂停
    ARCHIVED = "archived"       # 归档


class CustomerPriority(str, Enum):
    """客户优先级枚举"""
    HIGH = "high"       # 高优先级
    MEDIUM = "medium"   # 中优先级
    LOW = "low"         # 低优先级
