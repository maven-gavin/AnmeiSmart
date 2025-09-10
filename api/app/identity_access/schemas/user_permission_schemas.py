"""
用户权限相关的Pydantic模型

定义用户权限检查相关的请求和响应模型。
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class UserPermissionCheckResponse(BaseModel):
    """用户权限检查响应模型"""
    user_id: str = Field(..., description="用户ID")
    permission: str = Field(..., description="权限名称")
    has_permission: bool = Field(..., description="是否拥有权限")


class UserRoleCheckResponse(BaseModel):
    """用户角色检查响应模型"""
    user_id: str = Field(..., description="用户ID")
    role: str = Field(..., description="角色名称")
    has_role: bool = Field(..., description="是否拥有角色")


class UserPermissionsResponse(BaseModel):
    """用户权限列表响应模型"""
    user_id: str = Field(..., description="用户ID")
    permissions: List[str] = Field(..., description="权限列表")


class UserRolesResponse(BaseModel):
    """用户角色列表响应模型"""
    user_id: str = Field(..., description="用户ID")
    roles: List[str] = Field(..., description="角色列表")


class UserPermissionSummaryResponse(BaseModel):
    """用户权限摘要响应模型"""
    user_id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    roles: List[str] = Field(..., description="角色列表")
    permissions: List[str] = Field(..., description="权限列表")
    is_admin: bool = Field(..., description="是否为管理员")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    tenant_name: Optional[str] = Field(None, description="租户名称")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    created_at: datetime = Field(..., description="创建时间")
