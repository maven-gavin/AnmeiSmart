"""
资源相关的Pydantic模型

定义资源相关的请求和响应模型。
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.identity_access.enums import ResourceType


def to_camel(string: str) -> str:
    """将下划线命名转换为驼峰命名"""
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class ResourceBase(BaseModel):
    """资源基础模型，支持下划线和驼峰命名"""
    
    model_config = ConfigDict(
        populate_by_name=True,  # 允许使用字段名或别名
        alias_generator=to_camel,  # 自动生成驼峰别名
    )
    
    name: str = Field(..., description="资源名称，如 menu:home, api:user:create", max_length=100)
    display_name: Optional[str] = Field(None, description="资源显示名称", max_length=50)
    description: Optional[str] = Field(None, description="资源描述", max_length=255)
    resource_type: ResourceType = Field(ResourceType.API, description="资源类型：api 或 menu")
    resource_path: str = Field(..., description="API路径或菜单路径", max_length=255)
    http_method: Optional[str] = Field(None, description="HTTP方法：GET, POST, PUT, DELETE（仅API资源）", max_length=10)
    parent_id: Optional[str] = Field(None, description="父资源ID（菜单层级）")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    priority: int = Field(0, description="资源优先级")
    
    @field_validator('parent_id', 'tenant_id', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        """将空字符串转换为 None，避免外键约束错误"""
        if v == '' or (isinstance(v, str) and not v.strip()):
            return None
        return v


class ResourceCreate(ResourceBase):
    """创建资源请求模型"""
    pass


class ResourceUpdate(BaseModel):
    """更新资源请求模型，支持下划线和驼峰命名"""
    
    model_config = ConfigDict(
        populate_by_name=True,  # 允许使用字段名或别名
        alias_generator=to_camel,  # 自动生成驼峰别名
    )
    
    display_name: Optional[str] = Field(None, description="资源显示名称", max_length=50)
    description: Optional[str] = Field(None, description="资源描述", max_length=255)
    resource_path: Optional[str] = Field(None, description="API路径或菜单路径", max_length=255)
    http_method: Optional[str] = Field(None, description="HTTP方法：GET, POST, PUT, DELETE（仅API资源）", max_length=10)
    priority: Optional[int] = Field(None, description="资源优先级")


class ResourceResponse(ResourceBase):
    """资源响应模型"""
    id: str = Field(..., description="资源ID")
    is_active: bool = Field(..., description="是否启用")
    is_system: bool = Field(..., description="是否系统资源")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class ResourceListResponse(BaseModel):
    """资源列表响应模型"""
    resources: List[ResourceResponse] = Field(..., description="资源列表")
    total: int = Field(..., description="总数量")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")


class ResourcePermissionAssign(BaseModel):
    """资源权限分配请求模型"""
    resource_id: str = Field(..., description="资源ID")
    permission_id: str = Field(..., description="权限ID")


class ResourcePermissionResponse(BaseModel):
    """资源权限响应模型"""
    resource_id: str = Field(..., description="资源ID")
    resource_name: str = Field(..., description="资源名称")
    resource_display_name: Optional[str] = Field(None, description="资源显示名称")
    permission_id: str = Field(..., description="权限ID")
    permission_name: str = Field(..., description="权限名称")
    permission_display_name: Optional[str] = Field(None, description="权限显示名称")


class SyncMenusRequest(BaseModel):
    """同步菜单资源请求模型"""
    menus: List[dict] = Field(..., description="菜单列表")
    version: Optional[str] = Field(None, description="版本号")


class SyncMenusResponse(BaseModel):
    """同步菜单资源响应模型"""
    synced_count: int = Field(..., description="同步的资源数量")
    created_count: int = Field(..., description="新创建的资源数量")
    updated_count: int = Field(..., description="更新的资源数量")

