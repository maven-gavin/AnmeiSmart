from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List

from app.identity_access.schemas.user import UserCreate, UserUpdate, UserResponse, RoleResponse
from app.identity_access.infrastructure.db.user import User, Role
from app.identity_access.deps import get_identity_access_application_service
from app.identity_access.application import IdentityAccessApplicationService
from app.identity_access.deps import get_current_user
from app.common.infrastructure.db.base import get_db
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
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> ApiResponse[UserResponse]:
    """
    创建新用户
    
    需要管理员权限
    """
    try:
        # 检查当前用户是否有管理员权限
        can_manage = await identity_access_service.check_permission(
            str(current_user.id), "user:create"
        )
        if not can_manage:
            raise BusinessException(
                "没有足够的权限执行此操作",
                code=ErrorCode.PERMISSION_DENIED,
                status_code=status.HTTP_403_FORBIDDEN,
            )
        
        user = await identity_access_service.create_user(user_in)
        return ApiResponse.success(user, message="创建用户成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("创建用户失败", e)

@router.get("", response_model=ApiResponse[List[UserResponse]])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> ApiResponse[List[UserResponse]]:
    """
    获取用户列表
    
    需要管理员权限
    """
    try:
        # 检查当前用户是否有管理员权限
        can_read = await identity_access_service.check_permission(
            str(current_user.id), "user:read"
        )
        if not can_read:
            raise BusinessException(
                "没有足够的权限执行此操作",
                code=ErrorCode.PERMISSION_DENIED,
                status_code=status.HTTP_403_FORBIDDEN,
            )
        
        users = await identity_access_service.get_users_list(skip=skip, limit=limit)
        return ApiResponse.success(users, message="获取用户列表成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("获取用户列表失败", e)

@router.get("/me", response_model=ApiResponse[UserResponse])
async def read_user_me(
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> ApiResponse[UserResponse]:
    """获取当前用户信息"""
    try:
        user_response = await identity_access_service.get_user_by_id(str(current_user.id))
        if not user_response:
            raise BusinessException("用户不存在", code=ErrorCode.NOT_FOUND, status_code=status.HTTP_404_NOT_FOUND)
        return ApiResponse.success(user_response, message="获取当前用户成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("获取用户信息失败", e)

@router.put("/me", response_model=ApiResponse[UserResponse])
async def update_user_me(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> ApiResponse[UserResponse]:
    """更新当前用户信息"""
    try:
        # 移除任何角色更新尝试，普通用户不能更改自己的角色
        if hasattr(user_in, "roles"):
            delattr(user_in, "roles")
        
        user = await identity_access_service.update_user(
            user_id=str(current_user.id),
            user_data=user_in
        )
        return ApiResponse.success(user, message="更新当前用户成功")
    except ValueError as e:
        raise BusinessException(str(e), code=ErrorCode.VALIDATION_ERROR, status_code=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        raise _handle_unexpected_error("更新用户信息失败", e)

@router.get("/{user_id}", response_model=ApiResponse[UserResponse])
async def read_user_by_id(
    user_id: str,
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> ApiResponse[UserResponse]:
    """根据ID获取用户信息"""
    try:
        user = await identity_access_service.get_user_by_id(user_id)
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
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> ApiResponse[UserResponse]:
    """
    更新用户信息
    
    需要管理员权限
    """
    try:
        # 检查当前用户是否有管理员权限
        can_update = await identity_access_service.check_permission(
            str(current_user.id), "user:update"
        )
        if not can_update:
            raise BusinessException(
                "没有足够的权限执行此操作",
                code=ErrorCode.PERMISSION_DENIED,
                status_code=status.HTTP_403_FORBIDDEN,
            )
        
        user = await identity_access_service.update_user(
            user_id=user_id,
            user_data=user_in
        )
        return ApiResponse.success(user, message="更新用户成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("更新用户信息失败", e)

@router.get("/roles/all", response_model=ApiResponse[List[RoleResponse]])
async def read_roles(
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> ApiResponse[List[RoleResponse]]:
    """
    获取所有角色
    
    需要管理员权限
    """
    try:
        # 检查当前用户是否有管理员权限
        can_manage_roles = await identity_access_service.check_permission(
            str(current_user.id), "role:manage"
        )
        if not can_manage_roles:
            raise BusinessException(
                "没有足够的权限执行此操作",
                code=ErrorCode.PERMISSION_DENIED,
                status_code=status.HTTP_403_FORBIDDEN,
            )
        
        roles = await identity_access_service.get_all_roles()
        return ApiResponse.success(roles, message="获取角色列表成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("获取角色列表失败", e)

# ==================== 合并用户权限相关接口 ====================

@router.get("/{user_id}/permissions/check", response_model=ApiResponse[UserPermissionCheckResponse])
async def check_user_permission(
    user_id: str,
    permission: str = Query(..., description="要检查的权限名称"),
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service),
    db = Depends(get_db)
) -> ApiResponse[UserPermissionCheckResponse]:
    """检查用户是否有指定权限"""
    try:
        if current_user.id != user_id:
            if not await identity_access_service.is_user_admin_use_case(current_user.id):
                raise BusinessException(
                    "权限不足：只能检查自己的权限",
                    code=ErrorCode.PERMISSION_DENIED,
                    status_code=status.HTTP_403_FORBIDDEN
                )
        has_permission = await identity_access_service.check_user_permission(user_id, permission)
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
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service),
    db = Depends(get_db)
) -> ApiResponse[UserRoleCheckResponse]:
    """检查用户是否有指定角色"""
    try:
        if current_user.id != user_id:
            if not await identity_access_service.is_user_admin_use_case(current_user.id):
                raise BusinessException(
                    "权限不足：只能检查自己的角色",
                    code=ErrorCode.PERMISSION_DENIED,
                    status_code=status.HTTP_403_FORBIDDEN
                )
        has_role = await identity_access_service.check_user_role(user_id, role)
        return ApiResponse.success(UserRoleCheckResponse(
            user_id=user_id,
            role=role,
            has_role=has_role
        ))
    except Exception as e:
        raise _handle_unexpected_error("检查用户角色失败", e)


@router.get("/{user_id}/admin/check", response_model=ApiResponse[dict])
async def check_user_admin(
    user_id: str,
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service),
    db = Depends(get_db)
) -> ApiResponse[dict]:
    """检查用户是否为管理员"""
    try:
        if current_user.id != user_id:
            if not await identity_access_service.is_user_admin_use_case(current_user.id):
                raise BusinessException(
                    "权限不足：只能检查自己的管理员状态",
                    code=ErrorCode.PERMISSION_DENIED,
                    status_code=status.HTTP_403_FORBIDDEN
                )
        is_admin = await identity_access_service.is_user_admin(user_id)
        return ApiResponse.success({
            "user_id": user_id,
            "is_admin": is_admin
        })
    except Exception as e:
        raise _handle_unexpected_error("检查用户管理员状态失败", e)


@router.get("/{user_id}/permissions", response_model=ApiResponse[UserPermissionsResponse])
async def get_user_permissions(
    user_id: str,
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service),
    db = Depends(get_db)
) -> ApiResponse[UserPermissionsResponse]:
    """获取用户权限列表"""
    try:
        if current_user.id != user_id:
            if not await identity_access_service.is_user_admin_use_case(current_user.id):
                raise BusinessException(
                    "权限不足：只能查看自己的权限",
                    code=ErrorCode.PERMISSION_DENIED,
                    status_code=status.HTTP_403_FORBIDDEN
                )
        permissions = await identity_access_service.get_user_permissions(user_id)
        return ApiResponse.success(UserPermissionsResponse(
            user_id=user_id,
            permissions=permissions
        ))
    except Exception as e:
        raise _handle_unexpected_error("获取用户权限列表失败", e)


@router.get("/{user_id}/roles", response_model=ApiResponse[UserRolesResponse])
async def get_user_roles(
    user_id: str,
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service),
    db = Depends(get_db)
) -> ApiResponse[UserRolesResponse]:
    """获取用户角色列表"""
    try:
        if current_user.id != user_id:
            if not await identity_access_service.is_user_admin_use_case(current_user.id):
                raise BusinessException(
                    "权限不足：只能查看自己的角色",
                    code=ErrorCode.PERMISSION_DENIED,
                    status_code=status.HTTP_403_FORBIDDEN
                )
        roles = await identity_access_service.get_user_roles(user_id)
        return ApiResponse.success(UserRolesResponse(
            user_id=user_id,
            roles=roles
        ))
    except Exception as e:
        raise _handle_unexpected_error("获取用户角色列表失败", e)


@router.get("/{user_id}/permissions/summary", response_model=ApiResponse[UserPermissionSummaryResponse])
async def get_user_permission_summary(
    user_id: str,
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service),
    db = Depends(get_db)
) -> ApiResponse[UserPermissionSummaryResponse]:
    """获取用户权限摘要"""
    try:
        if current_user.id != user_id:
            if not await identity_access_service.is_user_admin_use_case(current_user.id):
                raise BusinessException(
                    "权限不足：只能查看自己的权限摘要",
                    code=ErrorCode.PERMISSION_DENIED,
                    status_code=status.HTTP_403_FORBIDDEN
                )
        summary = await identity_access_service.get_user_permission_summary(user_id)
        return ApiResponse.success(summary)
    except Exception as e:
        raise _handle_unexpected_error("获取用户权限摘要失败", e)