"""
资源管理控制器
"""
from fastapi import APIRouter, Depends, Query, status
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.common.deps import get_db
from app.identity_access.models.user import User
from app.identity_access.services.resource_service import ResourceService
from app.identity_access.services.resource_sync_service import ResourceSyncService
from app.identity_access.schemas.resource_schemas import (
    SyncMenusRequest, SyncMenusResponse, ResourceResponse, ResourceListResponse,
    ResourceCreate, ResourceUpdate
)
from app.identity_access.enums import ResourceType
from app.identity_access.deps.auth_deps import get_current_user, require_role
from app.core.api import ApiResponse, BusinessException, ErrorCode, SystemException

router = APIRouter()

def _handle_unexpected_error(message: str, exc: Exception) -> SystemException:
    return SystemException(message=message, code=ErrorCode.SYSTEM_ERROR)

def get_resource_service(db: Session = Depends(get_db)) -> ResourceService:
    return ResourceService(db)

@router.get("", response_model=ApiResponse[ResourceListResponse])
async def list_resources(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="限制数量"),
    resource_type: Optional[str] = Query(None, alias="resourceType", description="资源类型筛选：api 或 menu"),
    current_user: User = Depends(require_role("admin")),
    resource_service: ResourceService = Depends(get_resource_service)
) -> ApiResponse[ResourceListResponse]:
    """获取资源列表（全局，不区分租户）"""
    try:
        # 转换资源类型字符串为枚举
        resource_type_enum = None
        if resource_type:
            try:
                resource_type_enum = ResourceType(resource_type.lower())
            except ValueError:
                raise BusinessException(
                    f"无效的资源类型: {resource_type}。有效值: api, menu",
                    code=ErrorCode.INVALID_PARAMETER
                )
        
        # 获取所有资源（全局）
        all_resources = resource_service.get_all_resources(
            resource_type=resource_type_enum,
            is_active=None  # 不过滤激活状态
        )
        
        total = len(all_resources)
        
        # 分页
        paged_resources = all_resources[skip:skip + limit]
        
        # 转换为响应格式
        resource_responses = [
            ResourceResponse(
                id=resource.id,
                name=resource.name,
                display_name=resource.display_name,
                description=resource.description,
                resource_type=ResourceType(resource.resource_type),
                resource_path=resource.resource_path,
                http_method=resource.http_method,
                parent_id=resource.parent_id,
                priority=resource.priority,
                is_active=resource.is_active,
                is_system=resource.is_system,
                created_at=resource.created_at,
                updated_at=resource.updated_at,
            )
            for resource in paged_resources
        ]
        
        return ApiResponse.success(
            data=ResourceListResponse(
                resources=resource_responses,
                total=total,
                skip=skip,
                limit=limit
            ),
            message="获取资源列表成功"
        )
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("获取资源列表失败", e)

@router.get("/{resource_id}", response_model=ApiResponse[ResourceResponse])
async def get_resource(
    resource_id: str,
    current_user: User = Depends(require_role("admin")),
    resource_service: ResourceService = Depends(get_resource_service)
) -> ApiResponse[ResourceResponse]:
    """获取资源详情"""
    try:
        resource = resource_service.get_by_id(resource_id)
        if not resource:
            raise BusinessException("资源不存在", code=ErrorCode.NOT_FOUND, status_code=status.HTTP_404_NOT_FOUND)
        
        resource_response = ResourceResponse(
            id=resource.id,
            name=resource.name,
            display_name=resource.display_name,
            description=resource.description,
            resource_type=ResourceType(resource.resource_type),
            resource_path=resource.resource_path,
            http_method=resource.http_method,
            parent_id=resource.parent_id,
            priority=resource.priority,
            is_active=resource.is_active,
            is_system=resource.is_system,
            created_at=resource.created_at,
            updated_at=resource.updated_at,
        )
        
        return ApiResponse.success(resource_response, message="获取资源详情成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("获取资源详情失败", e)

@router.post("", response_model=ApiResponse[ResourceResponse], status_code=status.HTTP_201_CREATED)
async def create_resource(
    resource_in: ResourceCreate,
    current_user: User = Depends(require_role("admin")),
    resource_service: ResourceService = Depends(get_resource_service)
) -> ApiResponse[ResourceResponse]:
    """创建资源（全局，不区分租户）"""
    try:
        resource = resource_service.create_resource(resource_in)
        
        resource_response = ResourceResponse(
            id=resource.id,
            name=resource.name,
            display_name=resource.display_name,
            description=resource.description,
            resource_type=ResourceType(resource.resource_type),
            resource_path=resource.resource_path,
            http_method=resource.http_method,
            parent_id=resource.parent_id,
            priority=resource.priority,
            is_active=resource.is_active,
            is_system=resource.is_system,
            created_at=resource.created_at,
            updated_at=resource.updated_at,
        )
        
        return ApiResponse.success(resource_response, message="创建资源成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("创建资源失败", e)

@router.put("/{resource_id}", response_model=ApiResponse[ResourceResponse])
async def update_resource(
    resource_id: str,
    resource_in: ResourceUpdate,
    current_user: User = Depends(require_role("admin")),
    resource_service: ResourceService = Depends(get_resource_service)
) -> ApiResponse[ResourceResponse]:
    """更新资源（全局，不区分租户）"""
    try:
        resource = resource_service.update_resource(resource_id, resource_in)
        
        resource_response = ResourceResponse(
            id=resource.id,
            name=resource.name,
            display_name=resource.display_name,
            description=resource.description,
            resource_type=ResourceType(resource.resource_type),
            resource_path=resource.resource_path,
            http_method=resource.http_method,
            parent_id=resource.parent_id,
            priority=resource.priority,
            is_active=resource.is_active,
            is_system=resource.is_system,
            created_at=resource.created_at,
            updated_at=resource.updated_at,
        )
        
        return ApiResponse.success(resource_response, message="更新资源成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("更新资源失败", e)

@router.delete("/{resource_id}", status_code=status.HTTP_200_OK)
async def delete_resource(
    resource_id: str,
    current_user: User = Depends(require_role("admin")),
    resource_service: ResourceService = Depends(get_resource_service)
) -> ApiResponse[dict]:
    """删除资源（物理删除）"""
    try:
        resource = resource_service.get_by_id(resource_id)
        if not resource:
            raise BusinessException("资源不存在", code=ErrorCode.NOT_FOUND, status_code=status.HTTP_404_NOT_FOUND)
        
        # 系统资源不允许删除
        if resource.is_system:
            raise BusinessException("系统资源无法删除", code=ErrorCode.PERMISSION_DENIED, status_code=status.HTTP_403_FORBIDDEN)
        
        success = resource_service.delete_resource(resource_id)
        if not success:
            raise BusinessException("删除资源失败", code=ErrorCode.SYSTEM_ERROR)
        
        return ApiResponse.success({}, message="删除资源成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("删除资源失败", e)

@router.post("/sync-menus", response_model=ApiResponse[SyncMenusResponse])
async def sync_menus(
    request: SyncMenusRequest,
    current_user: User = Depends(require_role("admin")),
    resource_service: ResourceService = Depends(get_resource_service)
) -> ApiResponse[SyncMenusResponse]:
    """
    同步菜单资源到资源库
    需要管理员权限
    """
    try:
        resource_sync_service = ResourceSyncService(resource_service)
        
        result = await resource_sync_service.sync_menu_resources(request.menus)
        
        response = SyncMenusResponse(
            synced_count=result["synced_count"],
            created_count=result["created_count"],
            updated_count=result["updated_count"]
        )
        
        return ApiResponse.success(response, message="菜单资源同步成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("同步菜单资源失败", e)

