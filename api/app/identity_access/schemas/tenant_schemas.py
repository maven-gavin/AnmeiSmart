"""
租户相关的Pydantic模型

定义租户相关的请求和响应模型。
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from app.identity_access.domain.value_objects.tenant_status import TenantStatus
from app.identity_access.domain.value_objects.tenant_type import TenantType


class TenantBase(BaseModel):
    """租户基础模型"""
    name: str = Field(..., description="租户名称", max_length=50)
    display_name: Optional[str] = Field(None, description="租户显示名称", max_length=50)
    description: Optional[str] = Field(None, description="租户描述", max_length=255)
    tenant_type: TenantType = Field(TenantType.STANDARD, description="租户类型")
    contact_name: Optional[str] = Field(None, description="负责人姓名", max_length=50)
    contact_email: Optional[str] = Field(None, description="负责人邮箱", max_length=50)
    contact_phone: Optional[str] = Field(None, description="负责人联系电话", max_length=20)


class TenantCreate(TenantBase):
    """创建租户请求模型"""
    pass


class TenantUpdate(BaseModel):
    """更新租户请求模型"""
    display_name: Optional[str] = Field(None, description="租户显示名称", max_length=50)
    description: Optional[str] = Field(None, description="租户描述", max_length=255)
    contact_name: Optional[str] = Field(None, description="负责人姓名", max_length=50)
    contact_email: Optional[str] = Field(None, description="负责人邮箱", max_length=50)
    contact_phone: Optional[str] = Field(None, description="负责人联系电话", max_length=20)


class TenantResponse(TenantBase):
    """租户响应模型"""
    id: str = Field(..., description="租户ID")
    status: TenantStatus = Field(..., description="租户状态")
    is_active: bool = Field(..., description="是否启用")
    is_system: bool = Field(..., description="是否系统租户")
    is_admin: bool = Field(..., description="是否管理员租户")
    priority: int = Field(..., description="租户优先级")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class TenantListResponse(BaseModel):
    """租户列表响应模型"""
    tenants: List[TenantResponse] = Field(..., description="租户列表")
    total: int = Field(..., description="总数量")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")


class TenantStatisticsResponse(BaseModel):
    """租户统计信息响应模型"""
    tenant_id: str = Field(..., description="租户ID")
    tenant_name: str = Field(..., description="租户名称")
    user_count: int = Field(..., description="用户数量")
    role_count: int = Field(..., description="角色数量")
    permission_count: int = Field(..., description="权限数量")
    active_user_count: int = Field(..., description="活跃用户数量")
    created_at: datetime = Field(..., description="创建时间")
    last_activity: Optional[datetime] = Field(None, description="最后活动时间")
