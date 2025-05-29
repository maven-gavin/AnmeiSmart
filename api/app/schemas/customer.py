from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, EmailStr, Field, ConfigDict

# 客户基础信息
class CustomerBase(BaseModel):
    """顾客信息基础模型"""
    medical_history: Optional[str] = None
    allergies: Optional[str] = None
    preferences: Optional[str] = None

class CustomerCreate(CustomerBase):
    """创建顾客信息的请求模型"""
    user_id: str

class CustomerUpdate(CustomerBase):
    """更新顾客信息的请求模型"""
    pass

# 客户档案相关模型
class RiskNote(BaseModel):
    """风险提示模型"""
    type: str
    description: str
    level: Literal["high", "medium", "low"] = "medium"

class ConsultationHistoryItem(BaseModel):
    """咨询历史记录项模型"""
    date: str
    type: str
    description: str

class CustomerBasicInfo(BaseModel):
    """客户基本信息模型"""
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None

class CustomerProfileBase(BaseModel):
    """客户档案基础模型"""
    medical_history: Optional[str] = None
    allergies: Optional[str] = None
    preferences: Optional[str] = None
    tags: Optional[str] = None

class CustomerProfileCreate(CustomerProfileBase):
    """创建客户档案的请求模型"""
    customer_id: str

class CustomerProfileUpdate(CustomerProfileBase):
    """更新客户档案的请求模型"""
    risk_notes: Optional[List[RiskNote]] = None

class CustomerProfileInfo(BaseModel):
    """客户档案完整模型，与前端组件对应"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    basicInfo: CustomerBasicInfo
    riskNotes: Optional[List[RiskNote]] = None
    medical_history: Optional[str] = None
    allergies: Optional[str] = None
    preferences: Optional[str] = None
    tags: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @staticmethod
    def from_model(profile) -> "CustomerProfileInfo":
        if not profile:
            return None
        return CustomerProfileInfo(
            id=profile.id,
            basicInfo=CustomerBasicInfo(
                name=profile.name,
                age=profile.age,
                gender=profile.gender,
                phone=profile.phone
            ),
            riskNotes=[RiskNote(type=note.type, description=note.description, level=note.level) for note in getattr(profile, 'risk_notes', [])] if getattr(profile, 'risk_notes', None) else None,
            medical_history=profile.medical_history,
            allergies=profile.allergies,
            preferences=profile.preferences,
            tags=profile.tags.split(',') if profile.tags else None,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )

# 客户完整信息
class CustomerInfo(CustomerBase):
    """客户完整信息模型，包含基本用户信息"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    username: str
    email: str
    phone: Optional[str] = None
    avatar: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    profile: Optional[CustomerProfileInfo] = None

    @staticmethod
    def from_model(customer) -> "CustomerInfo":
        if not customer:
            return None
        return CustomerInfo(
            id=customer.id,
            user_id=customer.user_id,
            username=customer.username,
            email=customer.email,
            phone=customer.phone,
            avatar=customer.avatar,
            created_at=customer.created_at,
            updated_at=customer.updated_at,
            profile=CustomerProfileInfo.from_model(getattr(customer, 'profile', None))
        ) 