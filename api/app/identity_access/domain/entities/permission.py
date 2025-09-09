"""
权限实体

权限是身份与权限上下文中的实体，负责管理具体的权限配置。
"""

import uuid
from datetime import datetime
from typing import Optional, Set
from dataclasses import dataclass, field

from ..value_objects.permission_type import PermissionType
from ..value_objects.permission_scope import PermissionScope


@dataclass
class Permission:
    """权限实体"""
    
    # 身份标识
    id: str
    
    # 基本信息
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    
    # 权限类型和范围
    permission_type: PermissionType = PermissionType.ACTION
    scope: PermissionScope = PermissionScope.TENANT
    
    # 状态信息
    is_active: bool = True
    is_system: bool = False
    is_admin: bool = False
    
    # 优先级和租户关联
    priority: int = 0
    tenant_id: Optional[str] = None
    
    # 权限资源
    resource: Optional[str] = None
    action: Optional[str] = None
    
    # 时间戳
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """后初始化验证"""
        if not self.id or not self.id.strip():
            raise ValueError("权限ID不能为空")
        
        if not self.name or not self.name.strip():
            raise ValueError("权限名称不能为空")
        
        if len(self.name) > 50:
            raise ValueError("权限名称长度不能超过50个字符")
        
        # 验证权限类型和资源/动作的匹配
        if self.permission_type == PermissionType.ACTION and not self.action:
            raise ValueError("动作类型权限必须指定action")
        
        if self.permission_type == PermissionType.RESOURCE and not self.resource:
            raise ValueError("资源类型权限必须指定resource")
    
    @classmethod
    def create(
        cls,
        name: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        permission_type: PermissionType = PermissionType.ACTION,
        scope: PermissionScope = PermissionScope.TENANT,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        tenant_id: Optional[str] = None,
        is_system: bool = False,
        is_admin: bool = False
    ) -> "Permission":
        """创建新权限"""
        permission_id = str(uuid.uuid4())
        
        return cls(
            id=permission_id,
            name=name,
            display_name=display_name or name,
            description=description,
            permission_type=permission_type,
            scope=scope,
            resource=resource,
            action=action,
            tenant_id=tenant_id,
            is_system=is_system,
            is_admin=is_admin
        )
    
    @classmethod
    def create_system_permission(
        cls,
        name: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None
    ) -> "Permission":
        """创建系统权限"""
        return cls.create(
            name=name,
            display_name=display_name,
            description=description,
            resource=resource,
            action=action,
            scope=PermissionScope.SYSTEM,
            is_system=True,
            is_admin=True,
            priority=1000
        )
    
    def activate(self) -> None:
        """激活权限"""
        if self.is_active:
            raise ValueError("权限已经是激活状态")
        
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """停用权限"""
        if not self.is_active:
            raise ValueError("权限已经是停用状态")
        
        if self.is_system:
            raise ValueError("系统权限不能被停用")
        
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def update_info(
        self,
        display_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> None:
        """更新权限信息"""
        if display_name is not None:
            self.display_name = display_name
        if description is not None:
            self.description = description
        
        self.updated_at = datetime.utcnow()
    
    def can_be_deleted(self) -> bool:
        """检查权限是否可以被删除"""
        return not self.is_system
    
    def is_available(self) -> bool:
        """检查权限是否可用"""
        return self.is_active
    
    def is_system_permission(self) -> bool:
        """检查是否为系统权限"""
        return self.is_system
    
    def is_admin_permission(self) -> bool:
        """检查是否为管理员权限"""
        return self.is_admin
    
    def get_effective_name(self) -> str:
        """获取有效显示名称"""
        return self.display_name or self.name
    
    def get_permission_key(self) -> str:
        """获取权限键值（用于权限检查）"""
        if self.permission_type == PermissionType.ACTION and self.action:
            return f"{self.resource}:{self.action}" if self.resource else self.action
        elif self.permission_type == PermissionType.RESOURCE and self.resource:
            return self.resource
        else:
            return self.name
    
    def matches_permission(self, permission_key: str) -> bool:
        """检查是否匹配指定的权限键值"""
        return self.get_permission_key() == permission_key
    
    def __str__(self) -> str:
        return f"Permission(id={self.id}, name={self.name}, type={self.permission_type.value})"
    
    def __repr__(self) -> str:
        return f"Permission(id={self.id}, name={self.name}, scope={self.scope.value}, active={self.is_active})"
