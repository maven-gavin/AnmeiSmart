"""
租户状态值对象

定义租户的状态枚举。
"""

from enum import Enum


class TenantStatus(Enum):
    """租户状态枚举"""
    
    ACTIVE = "active"           # 激活
    INACTIVE = "inactive"       # 停用
    SUSPENDED = "suspended"     # 暂停
    PENDING = "pending"         # 待审核
    
    @classmethod
    def get_active_statuses(cls) -> list["TenantStatus"]:
        """获取激活状态列表"""
        return [cls.ACTIVE]
    
    @classmethod
    def get_inactive_statuses(cls) -> list["TenantStatus"]:
        """获取非激活状态列表"""
        return [cls.INACTIVE, cls.SUSPENDED, cls.PENDING]
    
    def is_active(self) -> bool:
        """检查是否为激活状态"""
        return self == self.ACTIVE
    
    def is_inactive(self) -> bool:
        """检查是否为非激活状态"""
        return self in self.get_inactive_statuses()
