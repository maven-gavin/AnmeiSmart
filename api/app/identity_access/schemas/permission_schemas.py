"""
权限相关的Pydantic模型

定义权限相关的请求和响应模型。
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from app.identity_access.enums import PermissionType
from app.identity_access.enums import PermissionScope


def to_camel(string: str) -> str:
    """将下划线命名转换为驼峰命名"""
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class PermissionBase(BaseModel):
    """权限基础模型，支持下划线和驼峰命名"""
    
    model_config = ConfigDict(
        populate_by_name=True,  # 允许使用字段名或别名
        alias_generator=to_camel,  # 自动生成驼峰别名
    )
    
    code: str = Field(..., description="权限标识码，如 user:create", max_length=100)
    name: str = Field(..., description="权限名称", max_length=50)
    display_name: Optional[str] = Field(None, description="权限显示名称", max_length=50)
    description: Optional[str] = Field(None, description="权限描述", max_length=255)
    permission_type: PermissionType = Field(PermissionType.ACTION, description="权限类型")
    scope: PermissionScope = Field(PermissionScope.TENANT, description="权限范围")
    is_active: Optional[bool] = Field(True, description="是否启用")
    is_system: Optional[bool] = Field(False, description="是否系统权限")
    is_admin: Optional[bool] = Field(False, description="是否管理员权限")
    priority: Optional[int] = Field(0, description="权限优先级")


class PermissionCreate(PermissionBase):
    """创建权限请求模型"""
    pass


class PermissionUpdate(BaseModel):
    """更新权限请求模型，支持下划线和驼峰命名"""
    
    model_config = ConfigDict(
        populate_by_name=True,  # 允许使用字段名或别名
        alias_generator=to_camel,  # 自动生成驼峰别名
    )
    
    code: Optional[str] = Field(None, description="权限标识码", max_length=100)
    name: Optional[str] = Field(None, description="权限名称", max_length=50)
    display_name: Optional[str] = Field(None, description="权限显示名称", max_length=50)
    description: Optional[str] = Field(None, description="权限描述", max_length=255)
    permission_type: Optional[PermissionType] = Field(None, description="权限类型")
    scope: Optional[PermissionScope] = Field(None, description="权限范围")
    is_active: Optional[bool] = Field(None, description="是否启用")
    is_system: Optional[bool] = Field(None, description="是否系统权限")
    is_admin: Optional[bool] = Field(None, description="是否管理员权限")
    priority: Optional[int] = Field(None, description="权限优先级")


class PermissionResponse(PermissionBase):
    """权限响应模型"""
    id: str = Field(..., description="权限ID")
    is_active: bool = Field(..., description="是否启用")
    is_system: bool = Field(..., description="是否系统权限")
    is_admin: bool = Field(..., description="是否管理员权限")
    priority: int = Field(..., description="权限优先级")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class PermissionListResponse(BaseModel):
    """权限列表响应模型"""
    permissions: List[PermissionResponse] = Field(..., description="权限列表")
    total: int = Field(..., description="总数量")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")


class RolePermissionAssign(BaseModel):
    """角色权限分配请求模型"""
    role_id: str = Field(..., description="角色ID")
    permission_id: str = Field(..., description="权限ID")


class RolePermissionResponse(BaseModel):
    """角色权限响应模型"""
    role_id: str = Field(..., description="角色ID")
    role_name: str = Field(..., description="角色名称")
    role_display_name: Optional[str] = Field(None, description="角色显示名称")
    permission_id: str = Field(..., description="权限ID")
    permission_name: str = Field(..., description="权限名称")
    permission_display_name: Optional[str] = Field(None, description="权限显示名称")
    assigned_at: datetime = Field(..., description="分配时间")


class ResourceIdsRequest(BaseModel):
    """资源ID列表请求模型"""
    resource_ids: List[str] = Field(..., description="资源ID列表", min_length=1)
