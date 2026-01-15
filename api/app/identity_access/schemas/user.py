from __future__ import annotations

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator

from app.identity_access.enums import AdminLevel

# 延迟导入避免循环依赖
if TYPE_CHECKING:
    from app.customer.schemas.customer import CustomerBase

def to_camel(string: str) -> str:
    """将下划线命名转换为驼峰命名"""
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class CamelModel(BaseModel):
    """启用驼峰别名的基础模型"""

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
    )


class RoleBase(CamelModel):
    """角色基础模型"""
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    tenant_id: Optional[str] = Field(default="system", description="租户ID")

class RoleCreate(RoleBase):
    """角色创建模型"""
    pass    

class RoleUpdate(CamelModel):
    """角色更新模型"""
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    tenant_id: Optional[str] = None
    is_active: Optional[bool] = None
    is_system: Optional[bool] = None
    is_admin: Optional[bool] = None
    priority: Optional[int] = None

class RoleResponse(RoleBase):
    """API响应中的角色模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    is_active: Optional[bool] = Field(default=True, description="是否启用")
    is_system: Optional[bool] = Field(default=False, description="是否系统角色")
    is_admin: Optional[bool] = Field(default=False, description="是否管理员角色")
    priority: Optional[int] = Field(default=0, description="角色优先级")
    tenant_id: Optional[str] = None
    tenant_name: Optional[str] = Field(None, description="租户名称")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @field_validator('is_active', 'is_system', 'is_admin', mode='before')
    @classmethod
    def validate_bool_fields(cls, v):
        """将 None 转换为默认布尔值"""
        if v is None:
            return False
        return bool(v)
    
    @field_validator('priority', mode='before')
    @classmethod
    def validate_priority(cls, v):
        """将 None 转换为默认优先级"""
        if v is None:
            return 0
        return int(v) if v is not None else 0

class UserBase(CamelModel):
    """用户基础模型"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    phone: Optional[str] = None
    avatar: Optional[str] = None
    is_active: bool = True

class OperatorBase(CamelModel):
    """运营人员信息基础模型"""
    department: Optional[str] = None
    responsibilities: Optional[str] = None

class AdminBase(CamelModel):
    """管理员信息基础模型"""
    admin_level: str = AdminLevel.BASIC  # 与数据库模型保持一致，使用枚举值
    access_permissions: Optional[str] = None

class UserCreate(UserBase):
    """用户创建模型"""
    password: str = Field(..., min_length=8)
    roles: List[str] = ["customer"]  # 默认为客户角色
    tenant_id: Optional[str] = "system"
    customer_info: Optional["CustomerBase"] = None
    operator_info: Optional[OperatorBase] = None
    admin_info: Optional[AdminBase] = None

class UserUpdate(CamelModel):
    """用户更新模型"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=8)
    phone: Optional[str] = None
    avatar: Optional[str] = None
    is_active: Optional[bool] = None
    roles: Optional[List[str]] = None
    tenant_id: Optional[str] = None
    customer_info: Optional["CustomerBase"] = None
    operator_info: Optional[OperatorBase] = None
    admin_info: Optional[AdminBase] = None

class ExtendedUserInfo(CamelModel):
    """扩展用户信息，包含角色特定信息"""
    customer_info: Optional["CustomerBase"] = None
    operator_info: Optional[OperatorBase] = None
    admin_info: Optional[AdminBase] = None

class UserResponse(UserBase):
    """API响应中的用户模型"""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=to_camel,
    )
    
    id: str
    tenant_id: str
    tenant_name: Optional[str] = None  # 租户名称
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    roles: List[str] = []
    permissions: List[str] = []
    active_role: Optional[str] = None
    extended_info: Optional[ExtendedUserInfo] = None

    @field_validator("roles", mode="before")
    @classmethod
    def normalize_roles(cls, value):
        """兼容 ORM Role 对象，确保 roles 是字符串列表"""
        if value is None:
            return []
        if isinstance(value, list):
            normalized = []
            for item in value:
                if isinstance(item, str):
                    normalized.append(item)
                else:
                    role_name = getattr(item, "name", None)
                    normalized.append(role_name if role_name is not None else str(item))
            return normalized
        return [str(value)]

class UserListItemResponse(CamelModel):
    """用户列表响应模型（宽松校验，避免历史数据导致列表失败）"""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=to_camel,
    )

    id: str
    tenant_id: str
    tenant_name: Optional[str] = None
    email: Optional[str] = None
    username: str
    phone: Optional[str] = None
    avatar: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    roles: List[str] = []
    active_role: Optional[str] = None
    extended_info: Optional[ExtendedUserInfo] = None

    @field_validator("roles", mode="before")
    @classmethod
    def normalize_list_roles(cls, value):
        """兼容 ORM Role 对象，确保 roles 是字符串列表"""
        if value is None:
            return []
        if isinstance(value, list):
            normalized = []
            for item in value:
                if isinstance(item, str):
                    normalized.append(item)
                else:
                    role_name = getattr(item, "name", None)
                    normalized.append(role_name if role_name is not None else str(item))
            return normalized
        return [str(value)]

class UserListResponse(CamelModel):
    """用户列表响应模型"""
    users: List[UserListItemResponse] = Field(..., description="用户列表")
    total: int = Field(..., description="总数量")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")

class SwitchRoleRequest(CamelModel):
    """角色切换请求模型"""
    role: str
    

# 重建所有使用前向引用的模型，确保 Pydantic 可以正确生成 OpenAPI schema
def _rebuild_models():
    """重建所有使用前向引用的模型"""
    try:
        # 尝试导入 CustomerBase 以解析前向引用
        from app.customer.schemas.customer import CustomerBase
        
        # 重建所有使用 CustomerBase 的模型
        UserCreate.model_rebuild()
        UserUpdate.model_rebuild()
        ExtendedUserInfo.model_rebuild()
    except ImportError:
        # 如果 CustomerBase 不可用，跳过重建（在 TYPE_CHECKING 时可能发生）
        pass

# 在模块加载时重建模型
_rebuild_models()
