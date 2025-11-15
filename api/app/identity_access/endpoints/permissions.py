"""
权限管理API端点

提供权限的CRUD操作和角色权限关联管理功能。
"""

from typing import List, Optional
import logging
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.common.infrastructure.db.base import get_db
from app.identity_access.deps.auth_deps import get_current_user
from app.identity_access.infrastructure.db.user import User
from app.identity_access.application.role_permission_application_service import RolePermissionApplicationService
from app.identity_access.deps.auth_deps import get_role_permission_application_service, get_identity_access_application_service
from app.identity_access.application.identity_access_application_service import IdentityAccessApplicationService
from app.identity_access.schemas.permission_schemas import (
    PermissionCreate,
    PermissionUpdate,
    PermissionResponse,
    PermissionListResponse,
    RolePermissionResponse,
)
from app.core.api import ApiResponse, BusinessException, ErrorCode, SystemException

router = APIRouter(prefix="/permissions", tags=["权限管理"])
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _handle_unexpected_error(message: str, exc: Exception) -> SystemException:
    logger.error(message, exc_info=True)
    return SystemException(message=message, code=ErrorCode.SYSTEM_ERROR)


@router.get("/", response_model=ApiResponse[PermissionListResponse])
async def list_permissions(
    tenant_id: Optional[str] = Query(None, description="租户ID筛选"),
    permission_type: Optional[str] = Query(None, description="权限类型筛选"),
    scope: Optional[str] = Query(None, description="权限范围筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    current_user: User = Depends(get_current_user),
    permission_service: RolePermissionApplicationService = Depends(get_role_permission_application_service),
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service),
    _db: Session = Depends(get_db),
) -> ApiResponse[PermissionListResponse]:
    """获取权限列表"""
    try:
        # 使用 IdentityAccessApplicationService 检查管理员权限
        if not await identity_service.is_user_admin(str(current_user.id)):
            if tenant_id and tenant_id != getattr(current_user, 'tenant_id', None):
                raise BusinessException(
                    message="权限不足：只能查看自己租户的权限",
                    code=ErrorCode.PERMISSION_DENIED,
                    status_code=status.HTTP_403_FORBIDDEN,
                )
            tenant_id = getattr(current_user, 'tenant_id', None)

        # 获取权限列表（注意：list_permissions 方法不支持所有筛选参数，需要先获取再过滤）
        all_permissions = await permission_service.list_permissions(tenant_id=tenant_id)
        
        # 前端筛选
        permissions = all_permissions
        if permission_type:
            permissions = [p for p in permissions if p.get('permission_type') == permission_type]
        if scope:
            permissions = [p for p in permissions if p.get('scope') == scope]
        if is_active is not None:
            permissions = [p for p in permissions if p.get('is_active') == is_active]
        
        # 分页
        total = len(permissions)
        permissions = permissions[skip:skip + limit]

        # 将字典转换为 PermissionResponse 对象
        permission_responses = [
            PermissionResponse(**p) for p in permissions
        ]
        
        response = PermissionListResponse(
            permissions=permission_responses,
            total=total,
            skip=skip,
            limit=limit,
        )
        return ApiResponse.success(data=response, message="获取权限列表成功")
    except BusinessException:
        raise
    except Exception as exc:
        raise _handle_unexpected_error("获取权限列表失败", exc) from exc


@router.get("/{permission_id}", response_model=ApiResponse[PermissionResponse])
async def get_permission(
    permission_id: str,
    current_user: User = Depends(get_current_user),
    permission_service: RolePermissionApplicationService = Depends(get_role_permission_application_service),
    _db: Session = Depends(get_db),
) -> ApiResponse[PermissionResponse]:
    """获取权限详情"""
    try:
        permission = await permission_service.get_permission_use_case(permission_id)
        if not permission:
            raise BusinessException(
                message="权限不存在",
                code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # 权限检查：系统管理员或租户管理员
        if not await permission_service.is_user_admin(current_user.id):
            if permission.tenant_id != current_user.tenant_id:
                raise BusinessException(
                    message="权限不足：只能查看自己租户的权限",
                    code=ErrorCode.PERMISSION_DENIED,
                    status_code=status.HTTP_403_FORBIDDEN,
                )

        return ApiResponse.success(data=permission, message="获取权限详情成功")
    except BusinessException:
        raise
    except Exception as exc:
        raise _handle_unexpected_error("获取权限详情失败", exc) from exc


@router.post(
    "/",
    response_model=ApiResponse[PermissionResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_permission(
    permission_data: PermissionCreate,
    current_user: User = Depends(get_current_user),
    permission_service: RolePermissionApplicationService = Depends(get_role_permission_application_service),
    _db: Session = Depends(get_db),
) -> ApiResponse[PermissionResponse]:
    """创建新权限"""
    try:
        # 权限检查：系统管理员或租户管理员
        if not await permission_service.is_user_admin(current_user.id):
            if permission_data.tenant_id != current_user.tenant_id:
                raise BusinessException(
                    message="权限不足：只能为自己租户创建权限",
                    code=ErrorCode.PERMISSION_DENIED,
                    status_code=status.HTTP_403_FORBIDDEN,
                )

        permission = await permission_service.create_permission_use_case(
            name=permission_data.name,
            display_name=permission_data.display_name,
            description=permission_data.description,
            permission_type=permission_data.permission_type,
            scope=permission_data.scope,
            resource=permission_data.resource,
            action=permission_data.action,
            tenant_id=permission_data.tenant_id or current_user.tenant_id,
        )

        return ApiResponse.success(data=permission, message="创建权限成功")
    except ValueError as exc:
        raise BusinessException(
            message=str(exc),
            code=ErrorCode.VALIDATION_ERROR,
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc
    except BusinessException:
        raise
    except Exception as exc:
        raise _handle_unexpected_error("创建权限失败", exc) from exc


@router.put("/{permission_id}", response_model=ApiResponse[PermissionResponse])
async def update_permission(
    permission_id: str,
    permission_data: PermissionUpdate,
    current_user: User = Depends(get_current_user),
    permission_service: RolePermissionApplicationService = Depends(get_role_permission_application_service),
    _db: Session = Depends(get_db),
) -> ApiResponse[PermissionResponse]:
    """更新权限信息"""
    try:
        # 先获取权限信息进行权限检查
        existing_permission = await permission_service.get_permission_use_case(permission_id)
        if not existing_permission:
            raise BusinessException(
                message="权限不存在",
                code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # 权限检查：系统管理员或租户管理员
        if not await permission_service.is_user_admin(current_user.id):
            if existing_permission.tenant_id != current_user.tenant_id:
                raise BusinessException(
                    message="权限不足：只能更新自己租户的权限",
                    code=ErrorCode.PERMISSION_DENIED,
                    status_code=status.HTTP_403_FORBIDDEN,
                )

        permission = await permission_service.update_permission_use_case(
            permission_id=permission_id,
            display_name=permission_data.display_name,
            description=permission_data.description,
            resource=permission_data.resource,
            action=permission_data.action,
        )

        return ApiResponse.success(data=permission, message="更新权限成功")
    except ValueError as exc:
        raise BusinessException(
            message=str(exc),
            code=ErrorCode.VALIDATION_ERROR,
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc
    except BusinessException:
        raise
    except Exception as exc:
        raise _handle_unexpected_error("更新权限失败", exc) from exc


@router.delete("/{permission_id}", response_model=ApiResponse[bool])
async def delete_permission(
    permission_id: str,
    current_user: User = Depends(get_current_user),
    permission_service: RolePermissionApplicationService = Depends(get_role_permission_application_service),
    _db: Session = Depends(get_db),
) -> ApiResponse[bool]:
    """删除权限"""
    try:
        # 先获取权限信息进行权限检查
        existing_permission = await permission_service.get_permission_use_case(permission_id)
        if not existing_permission:
            raise BusinessException(
                message="权限不存在",
                code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # 权限检查：系统管理员或租户管理员
        if not await permission_service.is_user_admin(current_user.id):
            if existing_permission.tenant_id != current_user.tenant_id:
                raise BusinessException(
                    message="权限不足：只能删除自己租户的权限",
                    code=ErrorCode.PERMISSION_DENIED,
                    status_code=status.HTTP_403_FORBIDDEN,
                )

        success = await permission_service.delete_permission_use_case(permission_id)
        if not success:
            raise BusinessException(
                message="权限不存在",
                code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return ApiResponse.success(data=True, message="权限删除成功")
    except ValueError as exc:
        raise BusinessException(
            message=str(exc),
            code=ErrorCode.VALIDATION_ERROR,
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc
    except BusinessException:
        raise
    except Exception as exc:
        raise _handle_unexpected_error("删除权限失败", exc) from exc


@router.post(
    "/{permission_id}/roles/{role_id}",
    response_model=ApiResponse[bool],
)
async def assign_permission_to_role(
    permission_id: str,
    role_id: str,
    current_user: User = Depends(get_current_user),
    permission_service: RolePermissionApplicationService = Depends(get_role_permission_application_service),
    _db: Session = Depends(get_db),
) -> ApiResponse[bool]:
    """为角色分配权限"""
    try:
        # 权限检查：系统管理员或租户管理员
        if not await permission_service.is_user_admin(current_user.id):
            raise BusinessException(
                message="权限不足：需要管理员权限",
                code=ErrorCode.PERMISSION_DENIED,
                status_code=status.HTTP_403_FORBIDDEN,
            )

        success = await permission_service.assign_permission_to_role_use_case(
            role_id=role_id,
            permission_id=permission_id,
        )

        if not success:
            raise BusinessException(
                message="分配权限失败：角色或权限不存在",
                code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return ApiResponse.success(data=True, message="权限分配成功")
    except BusinessException:
        raise
    except Exception as exc:
        raise _handle_unexpected_error("分配权限失败", exc) from exc


@router.delete(
    "/{permission_id}/roles/{role_id}",
    response_model=ApiResponse[bool],
)
async def remove_permission_from_role(
    permission_id: str,
    role_id: str,
    current_user: User = Depends(get_current_user),
    permission_service: RolePermissionApplicationService = Depends(get_role_permission_application_service),
    _db: Session = Depends(get_db),
) -> ApiResponse[bool]:
    """从角色移除权限"""
    try:
        # 权限检查：系统管理员或租户管理员
        if not await permission_service.is_user_admin(current_user.id):
            raise BusinessException(
                message="权限不足：需要管理员权限",
                code=ErrorCode.PERMISSION_DENIED,
                status_code=status.HTTP_403_FORBIDDEN,
            )

        success = await permission_service.remove_permission_from_role_use_case(
            role_id=role_id,
            permission_id=permission_id,
        )

        if not success:
            raise BusinessException(
                message="移除权限失败：角色或权限不存在",
                code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return ApiResponse.success(data=True, message="权限移除成功")
    except BusinessException:
        raise
    except Exception as exc:
        raise _handle_unexpected_error("移除权限失败", exc) from exc


@router.get(
    "/{permission_id}/roles",
    response_model=ApiResponse[List[RolePermissionResponse]],
)
async def get_permission_roles(
    permission_id: str,
    current_user: User = Depends(get_current_user),
    permission_service: RolePermissionApplicationService = Depends(get_role_permission_application_service),
    _db: Session = Depends(get_db),
) -> ApiResponse[List[RolePermissionResponse]]:
    """获取拥有指定权限的角色列表"""
    try:
        # 先检查权限是否存在
        permission = await permission_service.get_permission_use_case(permission_id)
        if not permission:
            raise BusinessException(
                message="权限不存在",
                code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # 权限检查：系统管理员或租户管理员
        if not await permission_service.is_user_admin(current_user.id):
            if permission.tenant_id != current_user.tenant_id:
                raise BusinessException(
                    message="权限不足：只能查看自己租户的权限角色",
                    code=ErrorCode.PERMISSION_DENIED,
                    status_code=status.HTTP_403_FORBIDDEN,
                )

        roles = await permission_service.get_permission_roles_use_case(permission_id)
        return ApiResponse.success(data=roles, message="获取权限角色成功")
    except BusinessException:
        raise
    except Exception as exc:
        raise _handle_unexpected_error("获取权限角色失败", exc) from exc
