from fastapi import APIRouter, Depends, Query, status
from typing import List, Optional

from app.identity_access.schemas.user import UserCreate, UserUpdate, UserResponse, RoleResponse, UserListResponse
from app.identity_access.models.user import User
from app.identity_access.services.user_service import UserService
from app.identity_access.services.role_service import RoleService
from app.identity_access.deps.user_deps import get_user_service, get_role_service
from app.identity_access.deps.auth_deps import get_current_user, require_role
from app.identity_access.schemas.user_permission_schemas import (
    UserPermissionCheckResponse, UserRoleCheckResponse,
    UserPermissionSummaryResponse, UserPermissionsResponse, UserRolesResponse
)
from app.core.api import ApiResponse, BusinessException, ErrorCode, SystemException

router = APIRouter()

def _handle_unexpected_error(message: str, exc: Exception) -> SystemException:
    return SystemException(message=message, code=ErrorCode.SYSTEM_ERROR)

@router.post("", response_model=ApiResponse[UserResponse], status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    current_user: User = Depends(require_role("administrator")), # 简化权限检查
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse[UserResponse]:
    """创建新用户"""
    try:
        user = await user_service.create_user(user_in)
        return ApiResponse.success(user, message="创建用户成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("创建用户失败", e)

@router.get("", response_model=ApiResponse[UserListResponse])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(require_role("administrator")),
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse[UserListResponse]:
    """获取用户列表"""
    try:
        # 获取用户列表和总数
        users = await user_service.get_users_list(skip=skip, limit=limit, search=search)
        total = await user_service.count_users(search=search)
        return ApiResponse.success(
            UserListResponse(users=users, total=total, skip=skip, limit=limit), 
            message="获取用户列表成功"
        )
    except Exception as e:
        raise _handle_unexpected_error("获取用户列表失败", e)

@router.get("/me", response_model=ApiResponse[UserResponse])
async def read_user_me(
    current_user: User = Depends(get_current_user)
) -> ApiResponse[UserResponse]:
    """获取当前用户信息"""
    return ApiResponse.success(current_user, message="获取当前用户成功")

@router.put("/me", response_model=ApiResponse[UserResponse])
async def update_user_me(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse[UserResponse]:
    """更新当前用户信息"""
    try:
        # 禁止更新角色
        if hasattr(user_in, "roles"):
            user_in.roles = None
        
        user = await user_service.update_user(current_user.id, user_in)
        return ApiResponse.success(user, message="更新当前用户成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("更新用户信息失败", e)

@router.get("/{user_id}", response_model=ApiResponse[UserResponse])
async def read_user_by_id(
    user_id: str,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse[UserResponse]:
    """根据ID获取用户信息"""
    try:
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise BusinessException("用户不存在", code=ErrorCode.NOT_FOUND, status_code=status.HTTP_404_NOT_FOUND)
        return ApiResponse.success(user, message="获取用户成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("获取用户信息失败", e)

@router.put("/{user_id}", response_model=ApiResponse[UserResponse])
async def update_user(
    user_id: str,
    user_in: UserUpdate,
    current_user: User = Depends(require_role("administrator")),
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse[UserResponse]:
    """更新用户信息 (管理员)"""
    try:
        user = await user_service.update_user(user_id, user_in)
        return ApiResponse.success(user, message="更新用户成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("更新用户信息失败", e)

@router.get("/roles/all", response_model=ApiResponse[List[RoleResponse]])
async def read_roles(
    current_user: User = Depends(require_role("administrator")),
    role_service: RoleService = Depends(get_role_service)
) -> ApiResponse[List[RoleResponse]]:
    """获取所有角色"""
    try:
        roles = role_service.get_all_roles()
        return ApiResponse.success(roles, message="获取角色列表成功")
    except Exception as e:
        raise _handle_unexpected_error("获取角色列表失败", e)

# ==================== 权限相关 ====================

@router.get("/{user_id}/permissions/check", response_model=ApiResponse[UserPermissionCheckResponse])
async def check_user_permission(
    user_id: str,
    permission: str = Query(..., description="要检查的权限名称"),
    current_user: User = Depends(get_current_user),
    role_service: RoleService = Depends(get_role_service)
) -> ApiResponse[UserPermissionCheckResponse]:
    """检查用户是否有指定权限"""
    try:
        has_permission = await role_service.check_permission(user_id, permission)
        return ApiResponse.success(UserPermissionCheckResponse(
            user_id=user_id,
            permission=permission,
            has_permission=has_permission
        ))
    except Exception as e:
        raise _handle_unexpected_error("检查用户权限失败", e)

@router.get("/{user_id}/roles/check", response_model=ApiResponse[UserRoleCheckResponse])
async def check_user_role(
    user_id: str,
    role: str = Query(..., description="要检查的角色名称"),
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse[UserRoleCheckResponse]:
    """检查用户是否有指定角色"""
    try:
        user = await user_service.get_user_by_id(user_id)
        has_role = False
        if user:
            has_role = any(r.name == role for r in user.roles)
            
        return ApiResponse.success(UserRoleCheckResponse(
            user_id=user_id,
            role=role,
            has_role=has_role
        ))
    except Exception as e:
        raise _handle_unexpected_error("检查用户角色失败", e)

@router.get("/{user_id}/roles", response_model=ApiResponse[UserRolesResponse])
async def get_user_roles(
    user_id: str,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse[UserRolesResponse]:
    """获取用户角色列表"""
    try:
        user = await user_service.get_user_by_id(user_id)
        roles = [r.name for r in user.roles] if user else []
        return ApiResponse.success(UserRolesResponse(
            user_id=user_id,
            roles=roles
        ))
    except Exception as e:
        raise _handle_unexpected_error("获取用户角色列表失败", e)

