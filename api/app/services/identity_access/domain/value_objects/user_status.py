"""
用户状态值对象

定义用户的状态枚举和业务规则。
"""

from enum import Enum
from typing import List


class UserStatus(Enum):
    """用户状态枚举"""
    
    ACTIVE = "active"           # 激活状态
    INACTIVE = "inactive"       # 未激活状态
    SUSPENDED = "suspended"     # 暂停状态
    DELETED = "deleted"         # 已删除状态
    
    @classmethod
    def from_bool(cls, is_active: bool) -> "UserStatus":
        """从布尔值创建状态"""
        return cls.ACTIVE if is_active else cls.INACTIVE
    
    def to_bool(self) -> bool:
        """转换为布尔值"""
        return self == UserStatus.ACTIVE
    
    def can_login(self) -> bool:
        """是否可以登录"""
        return self in [UserStatus.ACTIVE]
    
    def can_access_system(self) -> bool:
        """是否可以访问系统"""
        return self in [UserStatus.ACTIVE]
    
    def is_deleted(self) -> bool:
        """是否已删除"""
        return self == UserStatus.DELETED
    
    @classmethod
    def get_valid_statuses(cls) -> List["UserStatus"]:
        """获取有效状态列表"""
        return [cls.ACTIVE, cls.INACTIVE, cls.SUSPENDED]
    
    def __str__(self) -> str:
        return self.value
