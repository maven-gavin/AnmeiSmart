from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.identity_access.domain.enums import AdminLevel

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

class RoleCreate(RoleBase):
    """角色创建模型"""
    pass    

class RoleUpdate(CamelModel):
    """角色更新模型"""
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_system: Optional[bool] = None
    is_admin: Optional[bool] = None
    priority: Optional[int] = None

class RoleResponse(RoleBase):
    """API响应中的角色模型"""
    id: str
    is_active: bool = True
    is_system: bool = False
    is_admin: bool = False
    priority: int = 0
    tenant_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class UserBase(CamelModel):
    """用户基础模型"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    phone: Optional[str] = None
    avatar: Optional[str] = None
    is_active: bool = True

class DoctorBase(CamelModel):
    """医生信息基础模型"""
    specialization: Optional[str] = None
    certification: Optional[str] = None
    license_number: Optional[str] = None

class ConsultantBase(CamelModel):
    """顾问信息基础模型"""
    expertise: Optional[str] = None
    performance_metrics: Optional[str] = None

class OperatorBase(CamelModel):
    """运营人员信息基础模型"""
    department: Optional[str] = None
    responsibilities: Optional[str] = None

class AdministratorBase(CamelModel):
    """管理员信息基础模型"""
    admin_level: str = AdminLevel.BASIC  # 与数据库模型保持一致，使用枚举值
    access_permissions: Optional[str] = None

class UserCreate(UserBase):
    """用户创建模型"""
    password: str = Field(..., min_length=8)
    roles: List[str] = ["customer"]  # 默认为客户角色
    customer_info: Optional[CustomerBase] = None
    doctor_info: Optional[DoctorBase] = None
    consultant_info: Optional[ConsultantBase] = None
    operator_info: Optional[OperatorBase] = None
    administrator_info: Optional[AdministratorBase] = None

class UserUpdate(CamelModel):
    """用户更新模型"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=8)
    phone: Optional[str] = None
    avatar: Optional[str] = None
    roles: Optional[List[str]] = None
    customer_info: Optional[CustomerBase] = None
    doctor_info: Optional[DoctorBase] = None
    consultant_info: Optional[ConsultantBase] = None
    operator_info: Optional[OperatorBase] = None
    administrator_info: Optional[AdministratorBase] = None

class ExtendedUserInfo(CamelModel):
    """扩展用户信息，包含角色特定信息"""
    customer_info: Optional[CustomerBase] = None
    doctor_info: Optional[DoctorBase] = None
    consultant_info: Optional[ConsultantBase] = None
    operator_info: Optional[OperatorBase] = None
    administrator_info: Optional[AdministratorBase] = None

class UserResponse(UserBase):
    """API响应中的用户模型"""
    id: str
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    roles: List[str] = []
    active_role: Optional[str] = None
    extended_info: Optional[ExtendedUserInfo] = None

class UserListResponse(CamelModel):
    """用户列表响应模型"""
    users: List[UserResponse] = Field(..., description="用户列表")
    total: int = Field(..., description="总数量")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")

class SwitchRoleRequest(CamelModel):
    """角色切换请求模型"""
    role: str
    
