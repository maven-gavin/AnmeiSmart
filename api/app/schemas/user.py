from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class RoleBase(BaseModel):
    """角色基础模型"""
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    """角色创建模型"""
    pass

class RoleResponse(RoleBase):
    """API响应中的角色模型"""
    id: int

    @classmethod
    def from_orm(cls, role):
        return cls(
            id=role.id,
            name=role.name,
            description=role.description
        )

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    """用户基础模型"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    phone: Optional[str] = None
    avatar: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    """用户创建模型"""
    password: str = Field(..., min_length=8)
    roles: List[str] = []

class UserUpdate(BaseModel):
    """用户更新模型"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=8)
    phone: Optional[str] = None
    avatar: Optional[str] = None
    roles: Optional[List[str]] = None

class UserResponse(UserBase):
    """API响应中的用户模型"""
    id: int
    created_at: datetime
    roles: List[str] = []

    @classmethod
    def from_orm(cls, user):
        return cls(
            id=user.id,
            email=user.email,
            username=user.username, 
            phone=user.phone,
            avatar=user.avatar,
            is_active=user.is_active,
            created_at=user.created_at,
            roles=[role.name for role in user.roles]
        )   
    
