from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Any

from app.schemas.user import UserCreate, UserUpdate, UserResponse, RoleResponse
from app.db.models.user import User, Role
from app.services import user_service
from app.core.security import get_current_user
from app.db.base import get_db

router = APIRouter()

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    创建新用户
    
    需要管理员权限
    """
    # 检查当前用户是否有管理员权限
    user_roles = await user_service.get_user_roles(db, user_id=current_user.id)
    if "admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有足够的权限执行此操作"
        )
    
    user = await user_service.create(db, obj_in=user_in)
    return user

@router.get("/", response_model=List[UserResponse])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[UserResponse]:
    """
    获取用户列表
    
    需要管理员权限
    """
    # 检查当前用户是否有管理员权限
    user_roles = await user_service.get_user_roles(db, user_id=current_user.id)
    if "admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有足够的权限执行此操作"
        )
    
    # 修正查询语法，应该使用User的所有列或表示User的一个实例
    users = await user_service.get_multi(db, skip=skip, limit=limit)
    return users

@router.get("/me", response_model=UserResponse)
async def read_user_me(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """获取当前用户信息"""
    return UserResponse.from_model(current_user)

@router.put("/me", response_model=UserResponse)
async def update_user_me(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserResponse:
    """更新当前用户信息"""
    # 移除任何角色更新尝试，普通用户不能更改自己的角色
    if hasattr(user_in, "roles"):
        delattr(user_in, "roles")
        
    user = await user_service.update(db, user_id=current_user.id, obj_in=user_in)
    return user

@router.get("/{user_id}", response_model=UserResponse)
async def read_user_by_id(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserResponse:
    """根据ID获取用户信息"""
    user = await user_service.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    更新用户信息
    
    需要管理员权限
    """
    # 检查当前用户是否有管理员权限
    user_roles = await user_service.get_user_roles(db, user_id=current_user.id)
    if "admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有足够的权限执行此操作"
        )
    
    user = await user_service.update(db, user_id=user_id, obj_in=user_in)
    return user

@router.get("/roles/all", response_model=List[RoleResponse])
async def read_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[RoleResponse]:
    """
    获取所有角色
    
    需要管理员权限
    """
    # 检查当前用户是否有管理员权限
    user_roles = await user_service.get_user_roles(db, user_id=current_user.id)
    if "admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有足够的权限执行此操作"
        )
    
    roles = await user_service.get_roles(db)
    return roles 