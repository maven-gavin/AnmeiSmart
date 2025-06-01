from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.schemas.user import RoleCreate, RoleResponse, UserResponse
from app.db.models.user import Role, User
from app.services import user_service as crud_user
from app.core.security import get_current_user
from app.db.base import get_db

router = APIRouter()

@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_in: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoleResponse:
    """
    创建新角色
    
    需要管理员权限
    """
    # 检查当前用户是否有管理员权限
    user_roles = await crud_user.get_user_roles(db, user_id=current_user.id)
    if "admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有足够的权限执行此操作"
        )
    
    # 检查角色名是否已存在
    existing_role = await crud_user.get_role_by_name(db, name=role_in.name)
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"角色名 '{role_in.name}' 已存在"
        )
    
    # 创建新角色
    role = await crud_user.create_role(db, name=role_in.name, description=role_in.description)
    return role

@router.get("/", response_model=List[RoleResponse])
async def read_roles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[RoleResponse]:
    """
    获取角色列表
    
    需要登录
    """
    roles = await crud_user.get_roles(db)
    return roles

@router.get("/{role_id}", response_model=RoleResponse)
async def read_role(
    role_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoleResponse:
    """
    根据ID获取角色
    
    需要登录
    """
    role = await crud_user.get_role_by_id(db, role_id=role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    return role

@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    删除角色
    
    需要管理员权限
    """
    # 检查当前用户是否有管理员权限
    user_roles = await crud_user.get_user_roles(db, user_id=current_user.id)
    if "admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有足够的权限执行此操作"
        )
    
    # 获取角色
    role = await crud_user.get_role_by_id(db, role_id=role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    # 检查是否为系统基础角色（不允许删除）
    base_roles = ["admin", "consultant", "doctor", "customer", "operator"]
    if role.name in base_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除系统基础角色"
        )
    
    # 删除角色 - 需要通过 ORM 进行实际删除操作
    db_role = db.query(Role).filter(Role.id == role_id).first()
    db.delete(db_role)
    db.commit() 