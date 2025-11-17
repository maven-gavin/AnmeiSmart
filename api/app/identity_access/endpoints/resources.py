"""
资源管理API端点

提供资源的CRUD操作和资源权限关联管理功能。
"""

from typing import List, Optional
import logging
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.common.infrastructure.db.base import get_db
from app.identity_access.deps.auth_deps import get_current_user, get_resource_application_service
from app.identity_access.deps.permission_deps import require_admin
from app.identity_access.infrastructure.db.user import User
from app.identity_access.application.resource_application_service import ResourceApplicationService
from app.identity_access.application.identity_access_application_service import IdentityAccessApplicationService
from app.identity_access.deps.auth_deps import get_identity_access_application_service
from app.identity_access.schemas.resource_schemas import (
    ResourceCreate,
    ResourceUpdate,
    ResourceResponse,
    ResourceListResponse,
    SyncMenusRequest,
    SyncMenusResponse,
)
from app.identity_access.domain.value_objects.resource_type import ResourceType
from app.core.api import ApiResponse, BusinessException, ErrorCode, SystemException

router = APIRouter(prefix="/resources", tags=["资源管理"])
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _handle_unexpected_error(message: str, exc: Exception) -> SystemException:
    logger.error(message, exc_info=True)
    return SystemException(message=message, code=ErrorCode.SYSTEM_ERROR)


@router.get("/", response_model=ApiResponse[ResourceListResponse])
async def list_resources(
    tenant_id: Optional[str] = Query(None, description="租户ID筛选"),
    resource_type: Optional[str] = Query(None, description="资源类型筛选：api 或 menu"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    current_user: User = Depends(get_current_user),
    resource_service: ResourceApplicationService = Depends(get_resource_application_service),
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service),
    _db: Session = Depends(get_db),
) -> ApiResponse[ResourceListResponse]:
    """获取资源列表"""
    try:
        # 检查管理员权限
        if not await identity_service.is_user_admin(str(current_user.id)):
            if tenant_id and tenant_id != getattr(current_user, 'tenant_id', None):
                raise BusinessException(
                    message="权限不足：只能查看自己租户的资源",
                    code=ErrorCode.PERMISSION_DENIED,
                    status_code=status.HTTP_403_FORBIDDEN,
                )
            tenant_id = getattr(current_user, 'tenant_id', None)

        # 获取资源列表
        resources, total = await resource_service.list_resources(
            tenant_id=tenant_id,
            resource_type=resource_type,
            skip=skip,
            limit=limit
        )
        
        # 转换为响应模型
        resource_responses = [
            ResourceResponse(**r) for r in resources
        ]
        
        response = ResourceListResponse(
            resources=resource_responses,
            total=total,
            skip=skip,
            limit=limit,
        )
        return ApiResponse.success(data=response, message="获取资源列表成功")
    except BusinessException:
        raise
    except Exception as exc:
        raise _handle_unexpected_error("获取资源列表失败", exc) from exc


@router.get("/{resource_id}", response_model=ApiResponse[ResourceResponse])
@require_admin()
async def get_resource(
    resource_id: str,
    current_user: User = Depends(get_current_user),
    resource_service: ResourceApplicationService = Depends(get_resource_application_service),
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service),
    _db: Session = Depends(get_db),
) -> ApiResponse[ResourceResponse]:
    """获取资源详情"""
    try:

        resource = await resource_service.get_resource(resource_id)
        if not resource:
            raise BusinessException(
                message=f"资源不存在: {resource_id}",
                code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return ApiResponse.success(data=ResourceResponse(**resource), message="获取资源详情成功")
    except BusinessException:
        raise
    except Exception as exc:
        raise _handle_unexpected_error("获取资源详情失败", exc) from exc


@router.post("/", response_model=ApiResponse[ResourceResponse], status_code=status.HTTP_201_CREATED)
@require_admin()
async def create_resource(
    resource_data: ResourceCreate,
    current_user: User = Depends(get_current_user),
    resource_service: ResourceApplicationService = Depends(get_resource_application_service),
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service),
    _db: Session = Depends(get_db),
) -> ApiResponse[ResourceResponse]:
    """创建资源"""
    try:

        # 将空字符串转换为 None，避免外键约束错误
        parent_id = resource_data.parent_id if resource_data.parent_id else None
        tenant_id = resource_data.tenant_id if resource_data.tenant_id else getattr(current_user, 'tenant_id', None)
        
        resource = await resource_service.create_resource(
            name=resource_data.name,
            resource_type=ResourceType(resource_data.resource_type.value),
            resource_path=resource_data.resource_path,
            display_name=resource_data.display_name,
            description=resource_data.description,
            http_method=resource_data.http_method,
            parent_id=parent_id,
            tenant_id=tenant_id,
            is_system=False,
            priority=resource_data.priority
        )

        return ApiResponse.success(data=ResourceResponse(**resource), message="创建资源成功")
    except BusinessException:
        raise
    except ValueError as e:
        raise BusinessException(
            message=str(e),
            code=ErrorCode.VALIDATION_ERROR,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as exc:
        raise _handle_unexpected_error("创建资源失败", exc) from exc


@router.put("/{resource_id}", response_model=ApiResponse[ResourceResponse])
@require_admin()
async def update_resource(
    resource_id: str,
    resource_data: ResourceUpdate,
    current_user: User = Depends(get_current_user),
    resource_service: ResourceApplicationService = Depends(get_resource_application_service),
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service),
    _db: Session = Depends(get_db),
) -> ApiResponse[ResourceResponse]:
    """更新资源"""
    try:

        resource = await resource_service.update_resource(
            resource_id=resource_id,
            display_name=resource_data.display_name,
            description=resource_data.description,
            resource_path=resource_data.resource_path,
            http_method=resource_data.http_method,
            priority=resource_data.priority
        )

        return ApiResponse.success(data=ResourceResponse(**resource), message="更新资源成功")
    except BusinessException:
        raise
    except ValueError as e:
        raise BusinessException(
            message=str(e),
            code=ErrorCode.VALIDATION_ERROR,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as exc:
        raise _handle_unexpected_error("更新资源失败", exc) from exc


@router.delete("/{resource_id}", response_model=ApiResponse[dict])
@require_admin()
async def delete_resource(
    resource_id: str,
    current_user: User = Depends(get_current_user),
    resource_service: ResourceApplicationService = Depends(get_resource_application_service),
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service),
    _db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    """删除资源"""
    try:

        result = await resource_service.delete_resource(resource_id)
        if not result:
            raise BusinessException(
                message=f"资源不存在: {resource_id}",
                code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return ApiResponse.success(data={}, message="删除资源成功")
    except BusinessException:
        raise
    except ValueError as e:
        raise BusinessException(
            message=str(e),
            code=ErrorCode.VALIDATION_ERROR,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as exc:
        raise _handle_unexpected_error("删除资源失败", exc) from exc


@router.post("/sync-menus", response_model=ApiResponse[SyncMenusResponse])
@require_admin()
async def sync_menu_resources(
    request: SyncMenusRequest,
    current_user: User = Depends(get_current_user),
    resource_service: ResourceApplicationService = Depends(get_resource_application_service),
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service),
    _db: Session = Depends(get_db),
) -> ApiResponse[SyncMenusResponse]:
    """同步菜单资源"""
    try:

        result = await resource_service.sync_menu_resources(request.menus)

        response = SyncMenusResponse(
            synced_count=result["synced_count"],
            created_count=result["created_count"],
            updated_count=result["updated_count"]
        )

        return ApiResponse.success(data=response, message="同步菜单资源成功")
    except BusinessException:
        raise
    except Exception as exc:
        raise _handle_unexpected_error("同步菜单资源失败", exc) from exc

