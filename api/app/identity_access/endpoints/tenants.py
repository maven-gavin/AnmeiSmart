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

router = APIRouter(prefix="/tenants", tags=["租户管理"])


@router.get("", response_model=TenantListResponse)
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
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足：需要系统管理员权限"
            )
        
        # 使用正确的方法名，传递 tenant_status 参数（避免与 status 模块冲突）
        all_tenants = await tenant_service.list_tenants(status=tenant_status)
        
        # 筛选租户类型
        tenants = all_tenants
        if tenant_type:
            tenants = [t for t in tenants if t.get('tenant_type') == tenant_type]
        
        # 分页
        total = len(tenants)
        tenants = tenants[skip:skip + limit]
        
        # 转换为 TenantResponse
        tenant_responses = [TenantResponse(**t) for t in tenants]
        
        return TenantListResponse(
            tenants=tenant_responses,
            total=total,
            skip=skip,
            limit=limit
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取租户列表失败: {str(e)}"
        )


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
    tenant_service: TenantApplicationService = Depends(get_tenant_application_service),
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service),
    db: Session = Depends(get_db)
):
    """获取租户详情"""
    try:
        # 权限检查：系统管理员或租户管理员
        user_tenant_id = getattr(current_user, 'tenantId', None) or getattr(current_user, 'tenant_id', None)
        if not await identity_service.is_user_admin(str(current_user.id)):
            if user_tenant_id != tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足：只能查看自己租户的信息"
                )
        
        tenant_dict = await tenant_service.get_tenant(tenant_id)
        if not tenant_dict:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="租户不存在"
            )
        
        # 转换为 TenantResponse
        return TenantResponse(**tenant_dict)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取租户详情失败: {str(e)}"
        )


@router.post("", response_model=TenantResponse)
async def create_tenant(
    tenant_data: TenantCreate,
    current_user: User = Depends(get_current_user),
    tenant_service: TenantApplicationService = Depends(get_tenant_application_service),
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service),
    db: Session = Depends(get_db)
):
    """创建新租户"""
    try:
        # 权限检查：只有系统管理员可以创建租户
        if not await identity_service.is_user_admin(str(current_user.id)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足：需要系统管理员权限"
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
        
        # 转换为 TenantResponse
        return TenantResponse(**tenant_dict)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建租户失败: {str(e)}"
        )


@router.put("/{tenant_id}", response_model=TenantResponse)
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
        # 权限检查：系统管理员或租户管理员
        user_tenant_id = getattr(current_user, 'tenantId', None) or getattr(current_user, 'tenant_id', None)
        if not await identity_service.is_user_admin(str(current_user.id)):
            if user_tenant_id != tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足：只能更新自己租户的信息"
                )
        
        # 更新租户信息（包含基本信息和联系信息）
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="租户不存在"
            )
        
        # 转换为 TenantResponse
        return TenantResponse(**tenant_dict)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新租户失败: {str(e)}"
        )


@router.delete("/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
    tenant_service: TenantApplicationService = Depends(get_tenant_application_service),
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service),
    db: Session = Depends(get_db)
):
    """删除租户"""
    try:
        # 权限检查：只有系统管理员可以删除租户
        if not await identity_service.is_user_admin(str(current_user.id)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足：需要系统管理员权限"
            )
        
        success = await tenant_service.delete_tenant(tenant_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="租户不存在"
            )
        
        return {"message": "租户删除成功"}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除租户失败: {str(e)}"
        )


@router.post("/{tenant_id}/activate")
async def activate_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
    tenant_service: TenantApplicationService = Depends(get_tenant_application_service),
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service),
    db: Session = Depends(get_db)
):
    """激活租户"""
    try:
        # 权限检查：只有系统管理员可以激活租户
        if not await identity_service.is_user_admin(str(current_user.id)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足：需要系统管理员权限"
            )
        
        success = await tenant_service.activate_tenant(tenant_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="租户不存在"
            )
        
        return {"message": "租户激活成功"}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"激活租户失败: {str(e)}"
        )


@router.post("/{tenant_id}/deactivate")
async def deactivate_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
    tenant_service: TenantApplicationService = Depends(get_tenant_application_service),
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service),
    db: Session = Depends(get_db)
):
    """停用租户"""
    try:
        # 权限检查：只有系统管理员可以停用租户
        if not await identity_service.is_user_admin(str(current_user.id)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足：需要系统管理员权限"
            )
        
        success = await tenant_service.deactivate_tenant(tenant_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="租户不存在"
            )
        
        return {"message": "租户停用成功"}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"停用租户失败: {str(e)}"
        )


@router.get("/{tenant_id}/statistics", response_model=TenantStatisticsResponse)
async def get_tenant_statistics(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
    tenant_service: TenantApplicationService = Depends(get_tenant_application_service),
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service),
    db: Session = Depends(get_db)
):
    """获取租户统计信息"""
    try:
        # 权限检查：系统管理员或租户管理员
        user_tenant_id = getattr(current_user, 'tenantId', None) or getattr(current_user, 'tenant_id', None)
        if not await identity_service.is_user_admin(str(current_user.id)):
            if user_tenant_id != tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足：只能查看自己租户的统计信息"
                )
        
        statistics = await tenant_service.get_tenant_statistics(tenant_id)
        if not statistics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="租户不存在"
            )
        
        return statistics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取租户统计信息失败: {str(e)}"
        )
