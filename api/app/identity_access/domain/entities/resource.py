"""
资源实体

资源是身份与权限上下文中的实体，负责管理API端点和菜单项。
"""

import uuid
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass, field

from ..value_objects.resource_type import ResourceType


@dataclass
class ResourceEntity:
    """资源实体"""
    
    # 身份标识
    id: str
    
    # 基本信息
    name: str  # 资源名称，如 "menu:home", "api:user:create"
    displayName: Optional[str] = None
    description: Optional[str] = None
    
    # 资源类型和路径
    resourceType: ResourceType = ResourceType.API
    resourcePath: str = ""  # API路径或菜单路径
    httpMethod: Optional[str] = None  # GET, POST, PUT, DELETE（仅API资源）
    parentId: Optional[str] = None  # 父资源ID（菜单层级）
    
    # 状态信息
    isActive: bool = True
    isSystem: bool = False
    
    # 优先级和租户关联
    priority: int = 0
    tenantId: Optional[str] = None
    
    # 时间戳
    createdAt: datetime = field(default_factory=datetime.utcnow)
    updatedAt: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """后初始化验证"""
        if not self.id or not self.id.strip():
            raise ValueError("资源ID不能为空")
        
        if not self.name or not self.name.strip():
            raise ValueError("资源名称不能为空")
        
        if len(self.name) > 100:
            raise ValueError("资源名称长度不能超过100个字符")
        
        if not self.resourcePath or not self.resourcePath.strip():
            raise ValueError("资源路径不能为空")
        
        # 验证资源类型和HTTP方法
        if self.resourceType == ResourceType.API and not self.httpMethod:
            # API资源建议有HTTP方法，但不强制
            pass
        
        if self.resourceType == ResourceType.MENU and self.httpMethod:
            # 菜单资源不应该有HTTP方法
            self.httpMethod = None
        
        if self.displayName is None:
            self.displayName = self.name
    
    @classmethod
    def create(
        cls,
        name: str,
        resourceType: ResourceType,
        resourcePath: str,
        displayName: Optional[str] = None,
        description: Optional[str] = None,
        httpMethod: Optional[str] = None,
        parentId: Optional[str] = None,
        tenantId: Optional[str] = None,
        isSystem: bool = False,
        priority: int = 0
    ) -> "ResourceEntity":
        """创建新资源"""
        resource_id = str(uuid.uuid4())
        
        return cls(
            id=resource_id,
            name=name,
            displayName=displayName or name,
            description=description,
            resourceType=resourceType,
            resourcePath=resourcePath,
            httpMethod=httpMethod,
            parentId=parentId,
            tenantId=tenantId,
            isSystem=isSystem,
            priority=priority
        )
    
    @classmethod
    def create_api_resource(
        cls,
        name: str,
        resourcePath: str,
        httpMethod: str,
        displayName: Optional[str] = None,
        description: Optional[str] = None
    ) -> "ResourceEntity":
        """创建API资源"""
        return cls.create(
            name=name,
            resourceType=ResourceType.API,
            resourcePath=resourcePath,
            httpMethod=httpMethod,
            displayName=displayName,
            description=description,
            isSystem=True,
            tenantId=None
        )
    
    @classmethod
    def create_menu_resource(
        cls,
        name: str,
        resourcePath: str,
        displayName: Optional[str] = None,
        description: Optional[str] = None,
        parentId: Optional[str] = None
    ) -> "ResourceEntity":
        """创建菜单资源"""
        return cls.create(
            name=name,
            resourceType=ResourceType.MENU,
            resourcePath=resourcePath,
            displayName=displayName,
            description=description,
            parentId=parentId,
            isSystem=True,
            tenantId=None
        )
    
    def activate(self) -> None:
        """激活资源"""
        if self.isActive:
            raise ValueError("资源已经是激活状态")
        
        self.isActive = True
        self.updatedAt = datetime.utcnow()
    
    def deactivate(self) -> None:
        """停用资源"""
        if not self.isActive:
            raise ValueError("资源已经是停用状态")
        
        if self.isSystem:
            raise ValueError("系统资源不能被停用")
        
        self.isActive = False
        self.updatedAt = datetime.utcnow()
    
    def update_info(
        self,
        displayName: Optional[str] = None,
        description: Optional[str] = None,
        resourcePath: Optional[str] = None,
        httpMethod: Optional[str] = None,
        priority: Optional[int] = None
    ) -> None:
        """更新资源信息"""
        if displayName is not None:
            self.displayName = displayName
        if description is not None:
            self.description = description
        if resourcePath is not None:
            self.resourcePath = resourcePath
        if httpMethod is not None:
            self.httpMethod = httpMethod
        if priority is not None:
            self.priority = priority
        
        self.updatedAt = datetime.utcnow()
    
    def can_be_deleted(self) -> bool:
        """检查资源是否可以被删除"""
        return not self.isSystem
    
    def is_available(self) -> bool:
        """检查资源是否可用"""
        return self.isActive
    
    def is_system_resource(self) -> bool:
        """检查是否为系统资源"""
        return self.isSystem
    
    def is_api_resource(self) -> bool:
        """检查是否为API资源"""
        return self.resourceType == ResourceType.API
    
    def is_menu_resource(self) -> bool:
        """检查是否为菜单资源"""
        return self.resourceType == ResourceType.MENU
    
    def get_effective_name(self) -> str:
        """获取有效显示名称"""
        return self.displayName or self.name
    
    def __str__(self) -> str:
        return (
            f"ResourceEntity(id={self.id}, name={self.name}, displayName={self.displayName}, "
            f"resourceType={self.resourceType.value}, resourcePath={self.resourcePath}, "
            f"httpMethod={self.httpMethod}, isActive={self.isActive}, isSystem={self.isSystem}, "
            f"priority={self.priority}, tenantId={self.tenantId})"
        )
    
    def __repr__(self) -> str:
        return self.__str__()

