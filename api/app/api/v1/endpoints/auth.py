from datetime import timedelta
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, get_current_user
from app.db.base import get_db
from app.crud import crud_user
from app.models.token import Token
from app.models.user import User, UserCreate, UserUpdate

router = APIRouter()
settings = get_settings()

@router.post("/login", response_model=Token)
async def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    用户登录
    
    使用邮箱和密码登录系统，返回JWT令牌
    """
    user = await crud_user.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户未激活"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/register", response_model=User)
async def register(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    用户注册
    
    创建新用户，并返回用户信息
    """
    user = await crud_user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="此邮箱已注册",
        )
    
    user = await crud_user.create(db, obj_in=user_in)
    # 将用户角色转换为字符串列表
    user_dict = {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "phone": user.phone,
        "avatar": user.avatar,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "roles": [role.name for role in user.roles]
    }
    return user_dict

@router.post("/refresh-token", response_model=Token)
async def refresh_token(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    刷新令牌
    
    使用当前有效的令牌获取新的访问令牌
    """
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=current_user.id, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=User)
async def read_users_me(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    获取当前用户信息
    
    返回当前已认证用户的详细信息
    """
    # 将用户角色转换为字符串列表
    user_dict = {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "phone": current_user.phone,
        "avatar": current_user.avatar,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at,
        "roles": [role.name for role in current_user.roles]
    }
    return user_dict

@router.put("/me", response_model=User)
async def update_user_me(
    *,
    db: Session = Depends(get_db),
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    更新当前用户信息
    
    允许用户更新自己的信息
    """
    user = await crud_user.update(db, db_obj=current_user, obj_in=user_in)
    # 将用户角色转换为字符串列表
    user_dict = {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "phone": user.phone,
        "avatar": user.avatar,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "roles": [role.name for role in user.roles]
    }
    return user_dict

@router.get("/roles", response_model=List[str])
async def get_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    获取用户角色
    
    返回当前用户的所有角色
    """
    # 从数据库获取用户角色
    user_roles = await crud_user.get_user_roles(db, user_id=current_user.id)
    return user_roles 