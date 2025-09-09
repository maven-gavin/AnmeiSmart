"""
权限范围值对象

定义权限的作用范围枚举。
"""

from enum import Enum


class PermissionScope(Enum):
    """权限范围枚举"""
    
    SYSTEM = "system"           # 系统级权限
    TENANT = "tenant"           # 租户级权限
    USER = "user"               # 用户级权限
    RESOURCE = "resource"       # 资源级权限
    
    @classmethod
    def get_system_scopes(cls) -> list["PermissionScope"]:
        """获取系统级范围列表"""
        return [cls.SYSTEM]
    
    @classmethod
    def get_tenant_scopes(cls) -> list["PermissionScope"]:
        """获取租户级范围列表"""
        return [cls.TENANT]
    
    @classmethod
    def get_user_scopes(cls) -> list["PermissionScope"]:
        """获取用户级范围列表"""
        return [cls.USER]
    
    @classmethod
    def get_resource_scopes(cls) -> list["PermissionScope"]:
        """获取资源级范围列表"""
        return [cls.RESOURCE]
    
    def is_system_scope(self) -> bool:
        """检查是否为系统级范围"""
        return self == self.SYSTEM
    
    def is_tenant_scope(self) -> bool:
        """检查是否为租户级范围"""
        return self == self.TENANT
    
    def is_user_scope(self) -> bool:
        """检查是否为用户级范围"""
        return self == self.USER
    
    def is_resource_scope(self) -> bool:
        """检查是否为资源级范围"""
        return self == self.RESOURCE
    
    def get_hierarchy_level(self) -> int:
        """获取范围层级（数字越大范围越广）"""
        hierarchy_map = {
            self.USER: 1,
            self.RESOURCE: 2,
            self.TENANT: 3,
            self.SYSTEM: 4
        }
        return hierarchy_map.get(self, 0)
