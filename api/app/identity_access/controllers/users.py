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
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse[UserResponse]:
    """获取当前用户信息"""
    # 将 Role 对象列表转换为角色名称字符串列表
    roles = [role.name for role in current_user.roles] if current_user.roles else []
    
    # 获取活跃角色（从 JWT token 中获取，或使用默认角色）
    active_role = None
    if hasattr(current_user, '_active_role') and current_user._active_role:
        active_role = current_user._active_role
    else:
        # 尝试从用户服务获取默认角色
        try:
            active_role = await user_service.get_user_default_role(current_user.id)
        except:
            pass
        if not active_role and roles:
            active_role = roles[0]
    
    # 构建 UserResponse 数据
    user_data = {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "phone": current_user.phone,
        "avatar": current_user.avatar,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at,
        "last_login_at": getattr(current_user, 'last_login_at', None),
        "roles": roles,
        "active_role": active_role,
        "extended_info": None  # 可以后续扩展
    }
    
    user_response = UserResponse(**user_data)
    return ApiResponse.success(user_response, message="获取当前用户成功")

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

@router.get("/{user_id}/permissions/summary", response_model=ApiResponse[UserPermissionSummaryResponse])
async def get_user_permissions_summary(
    user_id: str,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    role_service: RoleService = Depends(get_role_service)
) -> ApiResponse[UserPermissionSummaryResponse]:
    """获取用户权限摘要"""
    try:
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise BusinessException("用户不存在", code=ErrorCode.NOT_FOUND, status_code=status.HTTP_404_NOT_FOUND)
        
        # 获取角色列表
        roles = [r.name for r in user.roles] if user.roles else []
        
        # 获取权限列表（从所有角色中收集）
        permissions = []
        is_admin = False
        for role in user.roles:
            if role.is_admin or role.name in ["administrator", "super_admin"]:
                is_admin = True
            # 收集角色的权限
            if role.permissions:
                for perm in role.permissions:
                    if perm.name not in permissions:
                        permissions.append(perm.name)
        
        # 获取租户信息
        tenant_id = user.tenant_id
        tenant_name = None
        if user.tenant:
            tenant_name = user.tenant.name
        
        summary = UserPermissionSummaryResponse(
            user_id=user.id,
            username=user.username,
            roles=roles,
            permissions=permissions,
            is_admin=is_admin,
            tenant_id=tenant_id,
            tenant_name=tenant_name,
            last_login_at=getattr(user, 'last_login_at', None),
            created_at=user.created_at
        )
        
        return ApiResponse.success(summary, message="获取用户权限摘要成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("获取用户权限摘要失败", e)

