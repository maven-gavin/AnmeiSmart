"""
角色实体

角色定义了系统中的权限和访问级别。
"""

import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Set

from ..value_objects.role_type import RoleType


@dataclass
class Role:
    """角色实体"""
    
    # 身份标识
    id: str
    
    # 基本信息
    name: str
    description: Optional[str] = None
    
    # 时间戳
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """后初始化验证"""
        if not self.id or not self.id.strip():
            raise ValueError("角色ID不能为空")
        
        if not self.name or not self.name.strip():
            raise ValueError("角色名称不能为空")
        
        # 验证角色名称是否有效
        valid_roles = [rt.value for rt in RoleType.get_all_roles()]
        if self.name not in valid_roles:
            raise ValueError(f"无效的角色名称: {self.name}")
    
    @classmethod
    def create(
        cls,
        name: str,
        description: Optional[str] = None
    ) -> "Role":
        """创建角色 - 工厂方法"""
        # 验证角色名称
        valid_roles = [rt.value for rt in RoleType.get_all_roles()]
        if name not in valid_roles:
            raise ValueError(f"无效的角色名称: {name}")
        
        return cls(
            id=str(uuid.uuid4()),
            name=name.strip(),
            description=description
        )
    
    def update_description(self, description: Optional[str]) -> None:
        """更新角色描述"""
        self.description = description
        self.updated_at = datetime.utcnow()
    
    def get_role_type(self) -> RoleType:
        """获取角色类型枚举"""
        try:
            return RoleType(self.name)
        except ValueError:
            raise ValueError(f"未知的角色类型: {self.name}")
    
    def get_permissions(self) -> Set[str]:
        """获取角色权限"""
        return self.get_role_type().get_permissions()
    
    def has_permission(self, permission: str) -> bool:
        """检查是否有特定权限"""
        return self.get_role_type().has_permission(permission)
    
    def is_admin_role(self) -> bool:
        """是否为管理员角色"""
        return self.get_role_type().is_admin()
    
    def is_medical_role(self) -> bool:
        """是否为医疗相关角色"""
        return self.get_role_type().is_medical()
    
    def can_manage_users(self) -> bool:
        """是否可以管理用户"""
        return self.get_role_type().can_manage_users()
    
    def can_access_admin_panel(self) -> bool:
        """是否可以访问管理面板"""
        return self.get_role_type().can_access_admin_panel()
    
    def __str__(self) -> str:
        return f"Role(id={self.id}, name={self.name})"
