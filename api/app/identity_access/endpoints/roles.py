from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

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
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(
        get_identity_access_application_service
    ),
) -> ApiResponse[List[RoleResponse]]:
    """
    获取角色列表

    需要登录
    """
    roles = await identity_access_service.get_all_roles()
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
    roles = await identity_access_service.get_all_roles()
    role = next((r for r in roles if r.id == role_id), None)
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
    db: Session = Depends(get_db),
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

    roles = await identity_access_service.get_all_roles()
    role = next((r for r in roles if r.id == role_id), None)
    if not role:
        raise BusinessException(
            "角色不存在",
            code=ErrorCode.NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if getattr(role, "is_system", False):
        raise BusinessException("不能删除系统基础角色")

    db_role = db.query(Role).filter(Role.id == role_id).first()
    if db_role:
        db.delete(db_role)
        db.commit()

    return ApiResponse.success(True, message="删除角色成功")