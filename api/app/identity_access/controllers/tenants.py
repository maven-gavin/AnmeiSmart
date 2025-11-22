from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status

from app.identity_access.schemas.tenant_schemas import TenantCreate, TenantUpdate, TenantResponse, TenantListResponse, TenantStatisticsResponse
from app.identity_access.models.user import Tenant, User
from app.identity_access.services.tenant_service import TenantService
from app.identity_access.deps.auth_deps import get_current_user, require_role
from app.common.deps import get_db
from app.core.api import ApiResponse, BusinessException, ErrorCode, SystemException
from sqlalchemy.orm import Session

router = APIRouter(prefix="/tenants", tags=["租户管理"])

def get_tenant_service(db: Session = Depends(get_db)) -> TenantService:
    return TenantService(db)

def _handle_unexpected_error(message: str, exc: Exception) -> SystemException:
    return SystemException(message=message, code=ErrorCode.SYSTEM_ERROR)

@router.get("", response_model=ApiResponse[TenantListResponse])
async def list_tenants(
    tenant_status: Optional[str] = Query(None, alias="status", description="租户状态筛选"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(require_role("administrator")),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """获取租户列表"""
    try:
        tenants = tenant_service.list_tenants(status=tenant_status)
        total = len(tenants)
        # 简单切片分页
        paged_tenants = tenants[skip:skip + limit]
        
        return ApiResponse.success(
            data=TenantListResponse(
                tenants=paged_tenants,
                total=total,
                skip=skip,
                limit=limit
            ),
            message="获取租户列表成功"
        )
    except Exception as e:
        raise _handle_unexpected_error("获取租户列表失败", e)

@router.get("/{tenant_id}", response_model=ApiResponse[TenantResponse])
async def get_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """获取租户详情"""
    try:
        # 简单权限检查：管理员或本租户用户
        is_admin = any(r.is_admin for r in current_user.roles)
        if not is_admin and current_user.tenant_id != tenant_id:
             raise BusinessException("权限不足", code=ErrorCode.PERMISSION_DENIED)
             
        tenant = tenant_service.get_tenant(tenant_id)
        if not tenant:
            raise BusinessException("租户不存在", code=ErrorCode.NOT_FOUND, status_code=status.HTTP_404_NOT_FOUND)
        return ApiResponse.success(tenant, message="获取租户详情成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("获取租户详情失败", e)

@router.post("", response_model=ApiResponse[TenantResponse])
async def create_tenant(
    tenant_in: TenantCreate,
    current_user: User = Depends(require_role("administrator")),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """创建新租户"""
    try:
        tenant = tenant_service.create_tenant(tenant_in)
        return ApiResponse.success(tenant, message="创建租户成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("创建租户失败", e)

@router.put("/{tenant_id}", response_model=ApiResponse[TenantResponse])
async def update_tenant(
    tenant_id: str,
    tenant_in: TenantUpdate,
    current_user: User = Depends(require_role("administrator")),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """更新租户"""
    try:
        tenant = tenant_service.update_tenant(tenant_id, tenant_in)
        return ApiResponse.success(tenant, message="更新租户成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("更新租户失败", e)

@router.delete("/{tenant_id}", response_model=ApiResponse[dict])
async def delete_tenant(
    tenant_id: str,
    current_user: User = Depends(require_role("administrator")),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """删除租户"""
    try:
        tenant_service.delete_tenant(tenant_id)
        return ApiResponse.success(data={"message": "租户删除成功"})
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("删除租户失败", e)

@router.post("/{tenant_id}/activate", response_model=ApiResponse[dict])
async def activate_tenant(
    tenant_id: str,
    current_user: User = Depends(require_role("administrator")),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """激活租户"""
    try:
        tenant_service.activate_tenant(tenant_id)
        return ApiResponse.success(data={"message": "租户激活成功"})
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("激活租户失败", e)

@router.post("/{tenant_id}/deactivate", response_model=ApiResponse[dict])
async def deactivate_tenant(
    tenant_id: str,
    current_user: User = Depends(require_role("administrator")),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """停用租户"""
    try:
        tenant_service.deactivate_tenant(tenant_id)
        return ApiResponse.success(data={"message": "租户停用成功"})
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("停用租户失败", e)

@router.get("/{tenant_id}/statistics", response_model=ApiResponse[TenantStatisticsResponse])
async def get_tenant_statistics(
    tenant_id: str,
    current_user: User = Depends(require_role("administrator")),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """获取租户统计信息"""
    try:
        stats = tenant_service.get_tenant_statistics(tenant_id)
        return ApiResponse.success(data=TenantStatisticsResponse(**stats), message="获取租户统计信息成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("获取租户统计信息失败", e)
