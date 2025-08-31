"""
管理员级别值对象

定义管理员权限级别。
"""

from enum import Enum
from typing import List, Set


class AdminLevel(Enum):
    """管理员级别枚举"""
    
    BASIC = "basic"    # 基础管理员
    SUPER = "super"    # 超级管理员
    
    def get_permissions(self) -> Set[str]:
        """获取管理员权限"""
        base_permissions = {
            "user:read",
            "user:update",
            "conversation:read",
            "conversation:update",
            "message:read",
            "customer:read",
            "customer:update",
            "system:monitor"
        }
        
        if self == AdminLevel.SUPER:
            super_permissions = {
                "user:create",
                "user:delete",
                "conversation:delete",
                "message:delete",
                "customer:create",
                "customer:delete",
                "system:admin",
                "role:manage",
                "system:config"
            }
            return base_permissions | super_permissions
        
        return base_permissions
    
    def has_permission(self, permission: str) -> bool:
        """检查是否有特定权限"""
        return permission in self.get_permissions()
    
    def can_manage_system(self) -> bool:
        """是否可以管理系统"""
        return self == AdminLevel.SUPER
    
    def can_manage_roles(self) -> bool:
        """是否可以管理角色"""
        return self == AdminLevel.SUPER
    
    def can_delete_data(self) -> bool:
        """是否可以删除数据"""
        return self == AdminLevel.SUPER
    
    @classmethod
    def get_all_levels(cls) -> List["AdminLevel"]:
        """获取所有级别"""
        return list(cls)
    
    def __str__(self) -> str:
        return self.value
