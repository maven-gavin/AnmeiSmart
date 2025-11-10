"""
权限实体

权限是身份与权限上下文中的实体，负责管理具体的权限配置。
"""

import uuid
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field

from ..value_objects.permission_type import PermissionType
from ..value_objects.permission_scope import PermissionScope


@dataclass
class PermissionEntity:
    """权限实体"""
    
    # 身份标识
    id: str
    
    # 基本信息
    name: str
    displayName: Optional[str] = None
    description: Optional[str] = None
    
    # 权限类型和范围
    permissionType: PermissionType = PermissionType.ACTION
    scope: PermissionScope = PermissionScope.TENANT
    
    # 状态信息
    isActive: bool = True
    isSystem: bool = False
    isAdmin: bool = False
    
    # 优先级和租户关联
    priority: int = 0
    tenantId: Optional[str] = None
    
    # 权限资源
    resource: Optional[str] = None
    action: Optional[str] = None
    
    # 时间戳
    createdAt: datetime = field(default_factory=datetime.utcnow)
    updatedAt: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """后初始化验证"""
        if not self.id or not self.id.strip():
            raise ValueError("权限ID不能为空")
        
        if not self.name or not self.name.strip():
            raise ValueError("权限名称不能为空")
        
        if len(self.name) > 50:
            raise ValueError("权限名称长度不能超过50个字符")
        
        # 验证权限类型和资源/动作的匹配
        if self.permissionType == PermissionType.ACTION and not self.action:
            raise ValueError("动作类型权限必须指定action")
        
        if self.permissionType == PermissionType.RESOURCE and not self.resource:
            raise ValueError("资源类型权限必须指定resource")
        
        if self.displayName is None:
            self.displayName = self.name
    
    @classmethod
    def create(
        cls,
        name: str,
        displayName: Optional[str] = None,
        description: Optional[str] = None,
        permissionType: PermissionType = PermissionType.ACTION,
        scope: PermissionScope = PermissionScope.TENANT,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        tenantId: Optional[str] = None,
        isSystem: bool = False,
        isAdmin: bool = False,
        priority: int = 0
    ) -> "PermissionEntity":
        """创建新权限"""
        permission_id = str(uuid.uuid4())
        
        return cls(
            id=permission_id,
            name=name,
            displayName=displayName or name,
            description=description,
            permissionType=permissionType,
            scope=scope,
            resource=resource,
            action=action,
            tenantId=tenantId,
            isSystem=isSystem,
            isAdmin=isAdmin,
            priority=priority
        )
    
    @classmethod
    def create_system_permission(
        cls,
        name: str,
        displayName: Optional[str] = None,
        description: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None
    ) -> "PermissionEntity":
        """创建系统权限"""
        return cls.create(
            name=name,
            displayName=displayName,
            description=description,
            resource=resource,
            action=action,
            scope=PermissionScope.SYSTEM,
            isSystem=True,
            isAdmin=True,
            priority=1000
        )
    
    def activate(self) -> None:
        """激活权限"""
        if self.isActive:
            raise ValueError("权限已经是激活状态")
        
        self.isActive = True
        self.updatedAt = datetime.utcnow()
    
    def deactivate(self) -> None:
        """停用权限"""
        if not self.isActive:
            raise ValueError("权限已经是停用状态")
        
        if self.isSystem:
            raise ValueError("系统权限不能被停用")
        
        self.isActive = False
        self.updatedAt = datetime.utcnow()
    
    def update_info(
        self,
        displayName: Optional[str] = None,
        description: Optional[str] = None
    ) -> None:
        """更新权限信息"""
        if displayName is not None:
            self.displayName = displayName
        if description is not None:
            self.description = description
        
        self.updatedAt = datetime.utcnow()
    
    def can_be_deleted(self) -> bool:
        """检查权限是否可以被删除"""
        return not self.isSystem
    
    def is_available(self) -> bool:
        """检查权限是否可用"""
        return self.isActive
    
    def is_system_permission(self) -> bool:
        """检查是否为系统权限"""
        return self.isSystem
    
    def is_admin_permission(self) -> bool:
        """检查是否为管理员权限"""
        return self.isAdmin
    
    def get_effective_name(self) -> str:
        """获取有效显示名称"""
        return self.displayName or self.name
    
    def get_permission_key(self) -> str:
        """获取权限键值（用于权限检查）"""
        if self.permissionType == PermissionType.ACTION and self.action:
            return f"{self.resource}:{self.action}" if self.resource else self.action
        elif self.permissionType == PermissionType.RESOURCE and self.resource:
            return self.resource
        else:
            return self.name
    
    def matches_permission(self, permission_key: str) -> bool:
        """检查是否匹配指定的权限键值"""
        return self.get_permission_key() == permission_key
    
    def __str__(self) -> str:
        return (
            f"PermissionEntity(id={self.id}, name={self.name}, displayName={self.displayName}, "
            f"description={self.description}, permissionType={self.permissionType.value}, "
            f"scope={self.scope.value}, resource={self.resource}, action={self.action}, "
            f"isActive={self.isActive}, isSystem={self.isSystem}, isAdmin={self.isAdmin}, "
            f"priority={self.priority}, tenantId={self.tenantId}, createdAt={self.createdAt}, "
            f"updatedAt={self.updatedAt})"
        )
    
    def __repr__(self) -> str:
        return (
            f"PermissionEntity(id={self.id}, name={self.name}, displayName={self.displayName}, "
            f"description={self.description}, permissionType={self.permissionType.value}, "
            f"scope={self.scope.value}, resource={self.resource}, action={self.action}, "
            f"isActive={self.isActive}, isSystem={self.isSystem}, isAdmin={self.isAdmin}, "
            f"priority={self.priority}, tenantId={self.tenantId}, createdAt={self.createdAt}, "
            f"updatedAt={self.updatedAt})"
        )
