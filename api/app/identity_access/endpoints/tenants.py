"""
租户管理API端点

提供租户的CRUD操作和权限管理功能。
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.common.infrastructure.db.base import get_db
from app.identity_access.deps.auth_deps import get_current_user, require_role, get_identity_access_application_service
from app.identity_access.infrastructure.db.user import User, Tenant
from app.identity_access.application.tenant_application_service import TenantApplicationService
from app.identity_access.deps.auth_deps import get_tenant_application_service
from app.identity_access.application.identity_access_application_service import IdentityAccessApplicationService
from app.identity_access.schemas.tenant_schemas import (
    TenantCreate, TenantUpdate, TenantResponse, TenantListResponse,
    TenantStatisticsResponse
)
from app.identity_access.domain.value_objects.tenant_status import TenantStatus
from app.core.api import ApiResponse, BusinessException, ErrorCode, SystemException

router = APIRouter(prefix="/tenants", tags=["租户管理"])

def _handle_unexpected_error(message: str, exc: Exception) -> SystemException:
    return SystemException(message=message, code=ErrorCode.SYSTEM_ERROR)

@router.get("", response_model=ApiResponse[TenantListResponse])
async def list_tenants(
    tenant_status: Optional[str] = Query(None, alias="status", description="租户状态筛选"),
    tenant_type: Optional[str] = Query(None, description="租户类型筛选"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    current_user: User = Depends(get_current_user),
    tenant_service: TenantApplicationService = Depends(get_tenant_application_service),
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service),
    db: Session = Depends(get_db)
):
    """获取租户列表"""
    try:
        # 权限检查：只有系统管理员可以查看所有租户
        if not await identity_service.is_user_admin(str(current_user.id)):
            raise BusinessException(
                message="权限不足：需要系统管理员权限",
                code=ErrorCode.PERMISSION_DENIED,
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        all_tenants = await tenant_service.list_tenants(status=tenant_status)
        
        tenants = all_tenants
        if tenant_type:
            tenants = [t for t in tenants if t.get('tenant_type') == tenant_type]
        
        total = len(tenants)
        tenants = tenants[skip:skip + limit]
        tenant_responses = [TenantResponse(**t) for t in tenants]
        
        return ApiResponse.success(
            data=TenantListResponse(
                tenants=tenant_responses,
                total=total,
                skip=skip,
                limit=limit
            ),
            message="获取租户列表成功"
        )
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("获取租户列表失败", e)


@router.get("/{tenant_id}", response_model=ApiResponse[TenantResponse])
async def get_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
    tenant_service: TenantApplicationService = Depends(get_tenant_application_service),
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service),
    db: Session = Depends(get_db)
):
    """获取租户详情"""
    try:
        user_tenant_id = getattr(current_user, 'tenantId', None) or getattr(current_user, 'tenant_id', None)
        if not await identity_service.is_user_admin(str(current_user.id)):
            if user_tenant_id != tenant_id:
                raise BusinessException(
                    message="权限不足：只能查看自己租户的信息",
                    code=ErrorCode.PERMISSION_DENIED,
                    status_code=status.HTTP_403_FORBIDDEN
                )
        
        tenant_dict = await tenant_service.get_tenant(tenant_id)
        if not tenant_dict:
            raise BusinessException(
                message="租户不存在",
                code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return ApiResponse.success(data=TenantResponse(**tenant_dict), message="获取租户详情成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("获取租户详情失败", e)


@router.post("", response_model=ApiResponse[TenantResponse])
async def create_tenant(
    tenant_data: TenantCreate,
    current_user: User = Depends(get_current_user),
    tenant_service: TenantApplicationService = Depends(get_tenant_application_service),
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service),
    db: Session = Depends(get_db)
):
    """创建新租户"""
    try:
        if not await identity_service.is_user_admin(str(current_user.id)):
            raise BusinessException(
                message="权限不足：需要系统管理员权限",
                code=ErrorCode.PERMISSION_DENIED,
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        tenant_dict = await tenant_service.create_tenant(
            name=tenant_data.name,
            display_name=tenant_data.display_name,
            description=tenant_data.description,
            tenant_type=tenant_data.tenant_type.value if hasattr(tenant_data.tenant_type, 'value') else tenant_data.tenant_type,
            status=tenant_data.status.value if tenant_data.status and hasattr(tenant_data.status, 'value') else (tenant_data.status if tenant_data.status else TenantStatus.ACTIVE.value),
            is_system=tenant_data.is_system if tenant_data.is_system is not None else False,
            is_admin=tenant_data.is_admin if tenant_data.is_admin is not None else False,
            priority=tenant_data.priority if tenant_data.priority is not None else 0,
            encrypted_pub_key=tenant_data.encrypted_pub_key,
            contact_name=tenant_data.contact_name,
            contact_email=tenant_data.contact_email,
            contact_phone=tenant_data.contact_phone
        )
        
        return ApiResponse.success(data=TenantResponse(**tenant_dict), message="创建租户成功")
    except BusinessException:
        raise
    except ValueError as e:
        raise BusinessException(str(e), code=ErrorCode.VALIDATION_ERROR, status_code=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        raise _handle_unexpected_error("创建租户失败", e)


@router.put("/{tenant_id}", response_model=ApiResponse[TenantResponse])
async def update_tenant(
    tenant_id: str,
    tenant_data: TenantUpdate,
    current_user: User = Depends(get_current_user),
    tenant_service: TenantApplicationService = Depends(get_tenant_application_service),
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service),
    db: Session = Depends(get_db)
):
    """更新租户信息"""
    try:
        user_tenant_id = getattr(current_user, 'tenantId', None) or getattr(current_user, 'tenant_id', None)
        if not await identity_service.is_user_admin(str(current_user.id)):
            if user_tenant_id != tenant_id:
                raise BusinessException(
                    message="权限不足：只能更新自己租户的信息",
                    code=ErrorCode.PERMISSION_DENIED,
                    status_code=status.HTTP_403_FORBIDDEN
                )
        
        tenant_dict = await tenant_service.update_tenant(
            tenant_id=tenant_id,
            name=tenant_data.name,
            display_name=tenant_data.display_name,
            description=tenant_data.description,
            tenant_type=tenant_data.tenant_type.value if tenant_data.tenant_type and hasattr(tenant_data.tenant_type, 'value') else tenant_data.tenant_type,
            status=tenant_data.status.value if tenant_data.status and hasattr(tenant_data.status, 'value') else tenant_data.status,
            is_system=tenant_data.is_system,
            is_admin=tenant_data.is_admin,
            priority=tenant_data.priority,
            encrypted_pub_key=tenant_data.encrypted_pub_key,
            contact_name=tenant_data.contact_name,
            contact_email=tenant_data.contact_email,
            contact_phone=tenant_data.contact_phone
        )
        
        if not tenant_dict:
            raise BusinessException(
                message="租户不存在",
                code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return ApiResponse.success(data=TenantResponse(**tenant_dict), message="更新租户成功")
    except BusinessException:
        raise
    except ValueError as e:
        raise BusinessException(str(e), code=ErrorCode.VALIDATION_ERROR, status_code=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        raise _handle_unexpected_error("更新租户失败", e)


@router.delete("/{tenant_id}", response_model=ApiResponse[dict])
async def delete_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
    tenant_service: TenantApplicationService = Depends(get_tenant_application_service),
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service),
    db: Session = Depends(get_db)
):
    """删除租户"""
    try:
        if not await identity_service.is_user_admin(str(current_user.id)):
            raise BusinessException(
                message="权限不足：需要系统管理员权限",
                code=ErrorCode.PERMISSION_DENIED,
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        success = await tenant_service.delete_tenant(tenant_id)
        if not success:
            raise BusinessException(
                message="租户不存在",
                code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return ApiResponse.success(data={"message": "租户删除成功"})
    except BusinessException:
        raise
    except ValueError as e:
        raise BusinessException(str(e), code=ErrorCode.VALIDATION_ERROR, status_code=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        raise _handle_unexpected_error("删除租户失败", e)


@router.post("/{tenant_id}/activate", response_model=ApiResponse[dict])
async def activate_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
    tenant_service: TenantApplicationService = Depends(get_tenant_application_service),
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service),
    db: Session = Depends(get_db)
):
    """激活租户"""
    try:
        if not await identity_service.is_user_admin(str(current_user.id)):
            raise BusinessException(
                message="权限不足：需要系统管理员权限",
                code=ErrorCode.PERMISSION_DENIED,
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        success = await tenant_service.activate_tenant(tenant_id)
        if not success:
            raise BusinessException(
                message="租户不存在",
                code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return ApiResponse.success(data={"message": "租户激活成功"})
    except BusinessException:
        raise
    except ValueError as e:
        raise BusinessException(str(e), code=ErrorCode.VALIDATION_ERROR, status_code=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        raise _handle_unexpected_error("激活租户失败", e)


@router.post("/{tenant_id}/deactivate", response_model=ApiResponse[dict])
async def deactivate_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
    tenant_service: TenantApplicationService = Depends(get_tenant_application_service),
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service),
    db: Session = Depends(get_db)
):
    """停用租户"""
    try:
        if not await identity_service.is_user_admin(str(current_user.id)):
            raise BusinessException(
                message="权限不足：需要系统管理员权限",
                code=ErrorCode.PERMISSION_DENIED,
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        success = await tenant_service.deactivate_tenant(tenant_id)
        if not success:
            raise BusinessException(
                message="租户不存在",
                code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return ApiResponse.success(data={"message": "租户停用成功"})
    except BusinessException:
        raise
    except ValueError as e:
        raise BusinessException(str(e), code=ErrorCode.VALIDATION_ERROR, status_code=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        raise _handle_unexpected_error("停用租户失败", e)


@router.get("/{tenant_id}/statistics", response_model=ApiResponse[TenantStatisticsResponse])
async def get_tenant_statistics(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
    tenant_service: TenantApplicationService = Depends(get_tenant_application_service),
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service),
    db: Session = Depends(get_db)
):
    """获取租户统计信息"""
    try:
        user_tenant_id = getattr(current_user, 'tenantId', None) or getattr(current_user, 'tenant_id', None)
        if not await identity_service.is_user_admin(str(current_user.id)):
            if user_tenant_id != tenant_id:
                raise BusinessException(
                    message="权限不足：只能查看自己租户的统计信息",
                    code=ErrorCode.PERMISSION_DENIED,
                    status_code=status.HTTP_403_FORBIDDEN
                )
        
        statistics = await tenant_service.get_tenant_statistics(tenant_id)
        if not statistics:
            raise BusinessException(
                message="租户不存在",
                code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return ApiResponse.success(data=TenantStatisticsResponse(**statistics), message="获取租户统计信息成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("获取租户统计信息失败", e)
