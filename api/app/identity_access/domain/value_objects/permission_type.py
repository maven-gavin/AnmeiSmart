"""
权限类型值对象

定义权限的类型枚举。
"""

from enum import Enum


class PermissionType(Enum):
    """权限类型枚举"""
    
    ACTION = "action"           # 动作权限（如：create, read, update, delete）
    RESOURCE = "resource"       # 资源权限（如：user, order, report）
    FEATURE = "feature"         # 功能权限（如：advanced_search, export_data）
    SYSTEM = "system"           # 系统权限（如：admin_access, system_config）
    
    @classmethod
    def get_action_types(cls) -> list["PermissionType"]:
        """获取动作类型列表"""
        return [cls.ACTION]
    
    @classmethod
    def get_resource_types(cls) -> list["PermissionType"]:
        """获取资源类型列表"""
        return [cls.RESOURCE]
    
    @classmethod
    def get_feature_types(cls) -> list["PermissionType"]:
        """获取功能类型列表"""
        return [cls.FEATURE]
    
    @classmethod
    def get_system_types(cls) -> list["PermissionType"]:
        """获取系统类型列表"""
        return [cls.SYSTEM]
    
    def is_action_type(self) -> bool:
        """检查是否为动作类型"""
        return self == self.ACTION
    
    def is_resource_type(self) -> bool:
        """检查是否为资源类型"""
        return self == self.RESOURCE
    
    def is_feature_type(self) -> bool:
        """检查是否为功能类型"""
        return self == self.FEATURE
    
    def is_system_type(self) -> bool:
        """检查是否为系统类型"""
        return self == self.SYSTEM
