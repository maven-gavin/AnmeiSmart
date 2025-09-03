from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from app.identity_access.domain.enums import AdminLevel

from app.customer.schemas.customer import CustomerBase

class RoleBase(BaseModel):
    """角色基础模型"""
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    """角色创建模型"""
    pass    

class RoleResponse(RoleBase):
    """API响应中的角色模型"""
    id: str

class UserBase(BaseModel):
    """用户基础模型"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    phone: Optional[str] = None
    avatar: Optional[str] = None
    is_active: bool = True

class DoctorBase(BaseModel):
    """医生信息基础模型"""
    specialization: Optional[str] = None
    certification: Optional[str] = None
    license_number: Optional[str] = None

class ConsultantBase(BaseModel):
    """顾问信息基础模型"""
    expertise: Optional[str] = None
    performance_metrics: Optional[str] = None

class OperatorBase(BaseModel):
    """运营人员信息基础模型"""
    department: Optional[str] = None
    responsibilities: Optional[str] = None

class AdministratorBase(BaseModel):
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

class UserUpdate(BaseModel):
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

class ExtendedUserInfo(BaseModel):
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


class SwitchRoleRequest(BaseModel):
    """角色切换请求模型"""
    role: str
    
