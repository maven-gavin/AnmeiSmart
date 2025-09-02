from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.identity_access.schemas.user import UserCreate, UserUpdate, UserResponse, RoleResponse
from app.identity_access.infrastructure.db.user import User, Role
from app.identity_access.deps.identity_access import get_identity_access_application_service
from app.identity_access.application import IdentityAccessApplicationService
from app.identity_access.deps.security_deps import get_current_user
from app.common.infrastructure.db.base import get_db

router = APIRouter()

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> UserResponse:
    """
    创建新用户
    
    需要管理员权限
    """
    try:
        # 检查当前用户是否有管理员权限
        can_manage = await identity_access_service.check_permission_use_case(
            str(current_user.id), "user:create"
        )
        if not can_manage:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有足够的权限执行此操作"
            )
        
        user = await identity_access_service.create_user_use_case(user_in)
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建用户失败"
        )

@router.get("/", response_model=List[UserResponse])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> List[UserResponse]:
    """
    获取用户列表
    
    需要管理员权限
    """
    try:
        # 检查当前用户是否有管理员权限
        can_read = await identity_access_service.check_permission_use_case(
            str(current_user.id), "user:read"
        )
        if not can_read:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有足够的权限执行此操作"
            )
        
        users = await identity_access_service.get_users_list_use_case(
            skip=skip, limit=limit
        )
        return users
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户列表失败"
        )

@router.get("/me", response_model=UserResponse)
async def read_user_me(
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> UserResponse:
    """获取当前用户信息"""
    try:
        user_response = await identity_access_service.get_user_by_id_use_case(str(current_user.id))
        if not user_response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        return user_response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户信息失败"
        )

@router.put("/me", response_model=UserResponse)
async def update_user_me(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> UserResponse:
    """更新当前用户信息"""
    try:
        # 移除任何角色更新尝试，普通用户不能更改自己的角色
        if hasattr(user_in, "roles"):
            delattr(user_in, "roles")
        
        user = await identity_access_service.update_user_use_case(
            user_id=str(current_user.id),
            user_data=user_in
        )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户信息失败"
        )

@router.get("/{user_id}", response_model=UserResponse)
async def read_user_by_id(
    user_id: str,
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> UserResponse:
    """根据ID获取用户信息"""
    try:
        user = await identity_access_service.get_user_by_id_use_case(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户信息失败"
        )

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> UserResponse:
    """
    更新用户信息
    
    需要管理员权限
    """
    try:
        # 检查当前用户是否有管理员权限
        can_update = await identity_access_service.check_permission_use_case(
            str(current_user.id), "user:update"
        )
        if not can_update:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有足够的权限执行此操作"
            )
        
        user = await identity_access_service.update_user_use_case(
            user_id=user_id,
            user_data=user_in
        )
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户信息失败"
        )

@router.get("/roles/all", response_model=List[RoleResponse])
async def read_roles(
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> List[RoleResponse]:
    """
    获取所有角色
    
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
        
        roles = await identity_access_service.get_all_roles_use_case()
        return roles
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取角色列表失败"
        ) 