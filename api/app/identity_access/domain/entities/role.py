"""
角色实体

角色定义了系统中的权限和访问级别，支持数据库配置管理。
"""

import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Set, List

from ..value_objects.role_type import RoleType


@dataclass
class Role:
    """角色实体"""
    
    # 身份标识
    id: str
    
    # 基本信息
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    
    # 状态信息
    is_active: bool = True
    is_system: bool = False
    is_admin: bool = False
    
    # 优先级和租户关联
    priority: int = 0
    tenant_id: Optional[str] = None
    
    # 时间戳
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """后初始化验证"""
        if not self.id or not self.id.strip():
            raise ValueError("角色ID不能为空")
        
        if not self.name or not self.name.strip():
            raise ValueError("角色名称不能为空")
        
        if len(self.name) > 50:
            raise ValueError("角色名称长度不能超过50个字符")
    
    @classmethod
    def create(
        cls,
        name: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        tenant_id: Optional[str] = None,
        is_system: bool = False,
        is_admin: bool = False
    ) -> "Role":
        """创建角色 - 工厂方法"""
        role_id = str(uuid.uuid4())
        
        return cls(
            id=role_id,
            name=name.strip(),
            display_name=display_name or name,
            description=description,
            tenant_id=tenant_id,
            is_system=is_system,
            is_admin=is_admin
        )
    
    @classmethod
    def create_system_role(
        cls,
        name: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        is_admin: bool = False
    ) -> "Role":
        """创建系统角色"""
        return cls.create(
            name=name,
            display_name=display_name,
            description=description,
            is_system=True,
            is_admin=is_admin,
            priority=1000
        )
    
    def activate(self) -> None:
        """激活角色"""
        if self.is_active:
            raise ValueError("角色已经是激活状态")
        
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """停用角色"""
        if not self.is_active:
            raise ValueError("角色已经是停用状态")
        
        if self.is_system:
            raise ValueError("系统角色不能被停用")
        
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def update_info(
        self,
        display_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> None:
        """更新角色信息"""
        if display_name is not None:
            self.display_name = display_name
        if description is not None:
            self.description = description
        
        self.updated_at = datetime.utcnow()
    
    def can_be_deleted(self) -> bool:
        """检查角色是否可以被删除"""
        return not self.is_system
    
    def is_available(self) -> bool:
        """检查角色是否可用"""
        return self.is_active
    
    def is_system_role(self) -> bool:
        """检查是否为系统角色"""
        return self.is_system
    
    def is_admin_role(self) -> bool:
        """检查是否为管理员角色"""
        return self.is_admin
    
    def get_effective_name(self) -> str:
        """获取有效显示名称"""
        return self.display_name or self.name
    
    def get_role_type(self) -> Optional[RoleType]:
        """获取角色类型枚举（如果存在）"""
        try:
            return RoleType(self.name)
        except ValueError:
            return None
    
    def get_legacy_permissions(self) -> Set[str]:
        """获取传统角色权限（向后兼容）"""
        role_type = self.get_role_type()
        if role_type:
            return role_type.get_permissions()
        return set()
    
    def has_legacy_permission(self, permission: str) -> bool:
        """检查是否有传统权限（向后兼容）"""
        return permission in self.get_legacy_permissions()
    
    def __str__(self) -> str:
        return f"Role(id={self.id}, name={self.name}, active={self.is_active})"
    
    def __repr__(self) -> str:
        return f"Role(id={self.id}, name={self.name}, system={self.is_system}, admin={self.is_admin})"
