from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.api import ApiResponse, BusinessException, ErrorCode
from app.identity_access.application import IdentityAccessApplicationService
from app.identity_access.deps import (
    get_current_user,
    get_identity_access_application_service,
)
from app.identity_access.infrastructure.db.user import Role, User
from app.identity_access.schemas.user import RoleCreate, RoleResponse, RoleUpdate
from app.common.infrastructure.db.base import get_db

router = APIRouter()


@router.post(
    "",
    response_model=ApiResponse[RoleResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_role(
    role_in: RoleCreate,
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(
        get_identity_access_application_service
    ),
) -> ApiResponse[RoleResponse]:
    """
    创建新角色

    需要管理员权限
    """
    can_manage_roles = await identity_access_service.check_permission(
        str(current_user.id), "role:manage"
    )
    if not can_manage_roles:
        raise BusinessException(
            "没有足够的权限执行此操作",
            code=ErrorCode.PERMISSION_DENIED,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    try:
        role = await identity_access_service.create_role(
            name=role_in.name,
            description=role_in.description,
        )
    except ValueError as exc:
        raise BusinessException(str(exc))

    return ApiResponse.success(role)


@router.get(
    "/",
    response_model=ApiResponse[List[RoleResponse]],
)
@router.get(
    "",
    response_model=ApiResponse[List[RoleResponse]],
)
async def read_roles(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="搜索关键词，支持搜索角色名称、显示名称、描述"),
    tenant_id: Optional[str] = Query(None, description="租户ID，系统管理员可指定查看其他租户的角色"),
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(
        get_identity_access_application_service
    ),
) -> ApiResponse[List[RoleResponse]]:
    """
    获取角色列表

    需要登录
    支持搜索参数：search - 搜索角色名称、显示名称、描述
    
    多租户支持：
    - 普通用户：自动返回当前用户所属租户的角色 + 系统角色
    - 系统管理员：可以通过tenant_id参数查看指定租户的角色
    """
    # 获取当前用户的租户ID
    # current_user可能是UserEntity（有tenantId）或User模型（有tenant_id）
    user_tenant_id = getattr(current_user, 'tenantId', None) or getattr(current_user, 'tenant_id', None)
    
    # 如果用户指定了tenant_id，检查是否为系统管理员
    if tenant_id and tenant_id != user_tenant_id:
        # 检查是否为系统管理员
        is_admin = await identity_access_service.check_permission(
            str(current_user.id), "role:manage"
        )
        if not is_admin:
            raise BusinessException(
                "只有系统管理员可以查看其他租户的角色",
                code=ErrorCode.PERMISSION_DENIED,
                status_code=status.HTTP_403_FORBIDDEN,
            )
        # 系统管理员可以查看指定租户的角色
        target_tenant_id = tenant_id
    else:
        # 使用当前用户的租户ID
        target_tenant_id = user_tenant_id
    
    # 获取角色列表（包含系统角色）
    roles = await identity_access_service.get_all_roles(
        search=search,
        tenant_id=target_tenant_id,
        include_system=True  # 始终包含系统角色
    )
    return ApiResponse.success(roles)


@router.get(
    "/{role_id}",
    response_model=ApiResponse[RoleResponse],
)
async def read_role(
    role_id: str,
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(
        get_identity_access_application_service
    ),
) -> ApiResponse[RoleResponse]:
    """
    根据ID获取角色

    需要登录
    """
    role = await identity_access_service.get_role_by_id(role_id)
    if not role:
        raise BusinessException(
            "角色不存在",
            code=ErrorCode.NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return ApiResponse.success(role)


@router.put(
    "/{role_id}",
    response_model=ApiResponse[RoleResponse],
)
async def update_role(
    role_id: str,
    role_in: RoleUpdate,
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(
        get_identity_access_application_service
    ),
) -> ApiResponse[RoleResponse]:
    """
    更新角色信息

    需要管理员权限
    """
    can_manage_roles = await identity_access_service.check_permission(
        str(current_user.id), "role:manage"
    )
    if not can_manage_roles:
        raise BusinessException(
            "没有足够的权限执行此操作",
            code=ErrorCode.PERMISSION_DENIED,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    try:
        updated_role = await identity_access_service.update_role(role_id, role_in)
    except ValueError as exc:
        raise BusinessException(str(exc))

    return ApiResponse.success(updated_role)


@router.delete(
    "/{role_id}",
    response_model=ApiResponse[bool],
)
async def delete_role(
    role_id: str,
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(
        get_identity_access_application_service
    ),
) -> ApiResponse[bool]:
    """
    删除角色

    需要管理员权限
    """
    can_manage_roles = await identity_access_service.check_permission(
        str(current_user.id), "role:manage"
    )
    if not can_manage_roles:
        raise BusinessException(
            "没有足够的权限执行此操作",
            code=ErrorCode.PERMISSION_DENIED,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    try:
        await identity_access_service.delete_role(role_id)
    except ValueError as exc:
        raise BusinessException(str(exc))

    return ApiResponse.success(True, message="删除角色成功")