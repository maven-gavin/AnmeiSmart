"""
角色类型值对象

定义系统角色类型和权限级别。
"""

from enum import Enum
from typing import List, Dict, Set


class RoleType(Enum):
    """角色类型枚举"""
    
    CUSTOMER = "customer"           # 客户
    CONSULTANT = "consultant"       # 顾问
    DOCTOR = "doctor"              # 医生
    OPERATOR = "operator"          # 运营人员
    ADMINISTRATOR = "administrator" # 管理员
    
    @classmethod
    def get_all_roles(cls) -> List["RoleType"]:
        """获取所有角色"""
        return list(cls)
    
    @classmethod
    def get_default_roles(cls) -> List["RoleType"]:
        """获取默认角色（公开注册用户）"""
        return [cls.CUSTOMER]
    
    @classmethod
    def get_admin_roles(cls) -> List["RoleType"]:
        """获取管理员角色"""
        return [cls.ADMINISTRATOR, cls.OPERATOR]
    
    @classmethod
    def get_medical_roles(cls) -> List["RoleType"]:
        """获取医疗相关角色"""
        return [cls.DOCTOR, cls.CONSULTANT]
    
    def get_permissions(self) -> Set[str]:
        """获取角色权限"""
        permissions = {
            RoleType.CUSTOMER: {
                "user:read:own",
                "user:update:own",
                "conversation:create",
                "conversation:read:own",
                "message:create",
                "message:read:own"
            },
            RoleType.CONSULTANT: {
                "user:read:own",
                "user:update:own",
                "conversation:create",
                "conversation:read:own",
                "conversation:read:assigned",
                "message:create",
                "message:read:own",
                "message:read:assigned",
                "customer:read:assigned"
            },
            RoleType.DOCTOR: {
                "user:read:own",
                "user:update:own",
                "conversation:create",
                "conversation:read:own",
                "conversation:read:assigned",
                "message:create",
                "message:read:own",
                "message:read:assigned",
                "customer:read:assigned",
                "medical:read",
                "medical:create",
                "medical:update"
            },
            RoleType.OPERATOR: {
                "user:read",
                "user:update",
                "conversation:read",
                "conversation:update",
                "message:read",
                "customer:read",
                "customer:update",
                "system:monitor"
            },
            RoleType.ADMINISTRATOR: {
                "user:read",
                "user:create",
                "user:update",
                "user:delete",
                "conversation:read",
                "conversation:update",
                "conversation:delete",
                "message:read",
                "message:delete",
                "customer:read",
                "customer:create",
                "customer:update",
                "customer:delete",
                "system:admin",
                "system:monitor",
                "role:manage"
            }
        }
        return permissions.get(self, set())
    
    def has_permission(self, permission: str) -> bool:
        """检查是否有特定权限"""
        return permission in self.get_permissions()
    
    def is_admin(self) -> bool:
        """是否为管理员角色"""
        return self in self.get_admin_roles()
    
    def is_medical(self) -> bool:
        """是否为医疗相关角色"""
        return self in self.get_medical_roles()
    
    def can_manage_users(self) -> bool:
        """是否可以管理用户"""
        return self.has_permission("user:create") or self.has_permission("user:delete")
    
    def can_access_admin_panel(self) -> bool:
        """是否可以访问管理面板"""
        return self.has_permission("system:admin")
    
    def __str__(self) -> str:
        return self.value
