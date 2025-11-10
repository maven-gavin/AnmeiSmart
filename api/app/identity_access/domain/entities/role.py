"""
角色实体

角色定义了系统中的权限和访问级别，支持数据库配置管理。
"""

import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Set

from ..value_objects.role_type import RoleType


@dataclass
class RoleEntity:
    """角色实体"""
    
    # 身份标识
    id: str
    
    # 基本信息
    name: str
    displayName: Optional[str] = None
    description: Optional[str] = None
    
    # 状态信息
    isActive: bool = True
    isSystem: bool = False
    isAdmin: bool = False
    
    # 优先级和租户关联
    priority: int = 0
    tenantId: Optional[str] = None
    
    # 时间戳
    createdAt: datetime = field(default_factory=datetime.utcnow)
    updatedAt: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """后初始化验证"""
        if not self.id or not self.id.strip():
            raise ValueError("角色ID不能为空")
        
        if not self.name or not self.name.strip():
            raise ValueError("角色名称不能为空")
        
        if len(self.name) > 50:
            raise ValueError("角色名称长度不能超过50个字符")
        
        if self.displayName is None:
            self.displayName = self.name
    
    @classmethod
    def create(
        cls,
        name: str,
        displayName: Optional[str] = None,
        description: Optional[str] = None,
        tenantId: Optional[str] = None,
        isSystem: bool = False,
        isAdmin: bool = False,
        priority: int = 0
    ) -> "RoleEntity":
        """创建角色 - 工厂方法"""
        role_id = str(uuid.uuid4())
        
        return cls(
            id=role_id,
            name=name.strip(),
            displayName=displayName or name,
            description=description,
            tenantId=tenantId,
            isSystem=isSystem,
            isAdmin=isAdmin,
            priority=priority
        )
    
    @classmethod
    def create_system_role(
        cls,
        name: str,
        displayName: Optional[str] = None,
        description: Optional[str] = None,
        isAdmin: bool = False
    ) -> "RoleEntity":
        """创建系统角色"""
        return cls.create(
            name=name,
            displayName=displayName,
            description=description,
            isSystem=True,
            isAdmin=isAdmin,
            priority=1000
        )
    
    def activate(self) -> None:
        """激活角色"""
        if self.isActive:
            raise ValueError("角色已经是激活状态")
        
        self.isActive = True
        self.updatedAt = datetime.utcnow()
    
    def deactivate(self) -> None:
        """停用角色"""
        if not self.isActive:
            raise ValueError("角色已经是停用状态")
        
        if self.isSystem:
            raise ValueError("系统角色不能被停用")
        
        self.isActive = False
        self.updatedAt = datetime.utcnow()
    
    def update_info(
        self,
        displayName: Optional[str] = None,
        description: Optional[str] = None
    ) -> None:
        """更新角色信息"""
        if displayName is not None:
            self.displayName = displayName
        if description is not None:
            self.description = description
        
        self.updatedAt = datetime.utcnow()
    
    def can_be_deleted(self) -> bool:
        """检查角色是否可以被删除"""
        return not self.isSystem
    
    def is_available(self) -> bool:
        """检查角色是否可用"""
        return self.isActive
    
    def is_system_role(self) -> bool:
        """检查是否为系统角色"""
        return self.isSystem
    
    def is_admin_role(self) -> bool:
        """检查是否为管理员角色"""
        return self.isAdmin
    
    def get_effective_name(self) -> str:
        """获取有效显示名称"""
        return self.displayName or self.name
    
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
        return f"RoleEntity(id={self.id}, name={self.name}, displayName={self.displayName}, description={self.description}, isActive={self.isActive}, isSystem={self.isSystem}, isAdmin={self.isAdmin}, priority={self.priority}, tenantId={self.tenantId}, createdAt={self.createdAt}, updatedAt={self.updatedAt})"
    
    def __repr__(self) -> str:
        return f"RoleEntity(id={self.id}, name={self.name}, displayName={self.displayName}, description={self.description}, isActive={self.isActive}, isSystem={self.isSystem}, isAdmin={self.isAdmin}, priority={self.priority}, tenantId={self.tenantId}, createdAt={self.createdAt}, updatedAt={self.updatedAt})"
