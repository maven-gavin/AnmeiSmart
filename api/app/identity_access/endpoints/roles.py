from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.identity_access.schemas.user import RoleCreate, RoleResponse, UserResponse
from app.identity_access.infrastructure.db.user import Role, User
from app.identity_access.deps.identity_access import get_identity_access_application_service
from app.identity_access.application import IdentityAccessApplicationService
from app.core.security import get_current_user
from app.common.infrastructure.db.base import get_db

router = APIRouter()

@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_in: RoleCreate,
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> RoleResponse:
    """
    创建新角色
    
    需要管理员权限
    """
    try:
        # 检查当前用户是否有管理员权限
        can_manage_roles = await identity_access_service.check_permission_use_case(
            str(current_user.id), "role:manage"
        )
        if not can_manage_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有足够的权限执行此操作"
            )
        
        # 创建新角色
        role = await identity_access_service.create_role_use_case(
            name=role_in.name, 
            description=role_in.description
        )
        return role
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建角色失败"
        )

@router.get("/", response_model=List[RoleResponse])
async def read_roles(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> List[RoleResponse]:
    """
    获取角色列表
    
    需要登录
    """
    try:
        roles = await identity_access_service.get_all_roles_use_case()
        return roles
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取角色列表失败"
        )

@router.get("/{role_id}", response_model=RoleResponse)
async def read_role(
    role_id: str,
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> RoleResponse:
    """
    根据ID获取角色
    
    需要登录
    """
    try:
        # 获取所有角色然后过滤
        roles = await identity_access_service.get_all_roles_use_case()
        role = next((r for r in roles if r.id == role_id), None)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        return role
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取角色失败"
        )

@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> None:
    """
    删除角色
    
    需要管理员权限
    """
    try:
        # 检查当前用户是否有管理员权限
        can_manage_roles = await identity_access_service.check_permission_use_case(
            str(current_user.id), "role:manage"
        )
        if not can_manage_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有足够的权限执行此操作"
            )
        
        # 获取角色信息
        roles = await identity_access_service.get_all_roles_use_case()
        role = next((r for r in roles if r.id == role_id), None)
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
        if db_role:
            db.delete(db_role)
            db.commit()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除角色失败"
        ) 