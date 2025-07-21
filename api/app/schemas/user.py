from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.schemas.customer import CustomerBase
from app.db.models.user import AdminLevel

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

    @classmethod
    def from_orm(cls, role):
        return cls(
            id=role.id,
            name=role.name,
            description=role.description
        )

    model_config = ConfigDict(from_attributes=True)

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
    roles: List[str] = []
    active_role: Optional[str] = None
    extended_info: Optional[ExtendedUserInfo] = None

    @staticmethod
    def from_model(user, active_role=None) -> "UserResponse":
        extended_info = ExtendedUserInfo()
        if getattr(user, 'doctor', None):
            extended_info.doctor_info = DoctorBase(
                specialization=user.doctor.specialization,
                certification=user.doctor.certification,
                license_number=user.doctor.license_number
            )
        if getattr(user, 'consultant', None):
            extended_info.consultant_info = ConsultantBase(
                expertise=user.consultant.expertise,
                performance_metrics=user.consultant.performance_metrics
            )
        if getattr(user, 'operator', None):
            extended_info.operator_info = OperatorBase(
                department=user.operator.department,
                responsibilities=user.operator.responsibilities
            )
        if getattr(user, 'administrator', None):
            extended_info.administrator_info = AdministratorBase(
                admin_level=user.administrator.admin_level,
                access_permissions=user.administrator.access_permissions
            )
        active_role = active_role or (user.roles[0].name if getattr(user, 'roles', None) else None)
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username, 
            phone=user.phone,
            avatar=user.avatar,
            is_active=user.is_active,
            created_at=user.created_at,
            roles=[role.name for role in user.roles] if getattr(user, 'roles', None) else [],
            active_role=active_role,
            extended_info=extended_info
        )

class SwitchRoleRequest(BaseModel):
    """角色切换请求模型"""
    role: str
    
