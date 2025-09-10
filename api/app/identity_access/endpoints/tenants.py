"""
租户管理API端点

提供租户的CRUD操作和权限管理功能。
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.common.infrastructure.db.base import get_db
from app.identity_access.deps.auth_deps import get_current_user, require_role
from app.identity_access.infrastructure.db.user import User, Tenant
from app.identity_access.application.tenant_application_service import TenantApplicationService
from app.identity_access.deps.auth_deps import get_tenant_application_service
from app.identity_access.schemas.tenant_schemas import (
    TenantCreate, TenantUpdate, TenantResponse, TenantListResponse,
    TenantStatisticsResponse
)

router = APIRouter(prefix="/tenants", tags=["租户管理"])


@router.get("/", response_model=TenantListResponse)
async def list_tenants(
    status: Optional[str] = Query(None, description="租户状态筛选"),
    tenant_type: Optional[str] = Query(None, description="租户类型筛选"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    current_user: User = Depends(get_current_user),
    tenant_service: TenantApplicationService = Depends(get_tenant_application_service),
    db: Session = Depends(get_db)
):
    """获取租户列表"""
    try:
        # 权限检查：只有系统管理员可以查看所有租户
        if not await tenant_service.is_user_admin(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足：需要系统管理员权限"
            )
        
        tenants = await tenant_service.list_tenants_use_case(
            status=status,
            tenant_type=tenant_type,
            skip=skip,
            limit=limit
        )
        
        return TenantListResponse(
            tenants=tenants,
            total=len(tenants),
            skip=skip,
            limit=limit
        )
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
    db: Session = Depends(get_db)
):
    """获取租户详情"""
    try:
        # 权限检查：系统管理员或租户管理员
        if not await tenant_service.is_user_admin(current_user.id):
            if current_user.tenant_id != tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足：只能查看自己租户的信息"
                )
        
        tenant = await tenant_service.get_tenant_use_case(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="租户不存在"
            )
        
        return tenant
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取租户详情失败: {str(e)}"
        )


@router.post("/", response_model=TenantResponse)
async def create_tenant(
    tenant_data: TenantCreate,
    current_user: User = Depends(get_current_user),
    tenant_service: TenantApplicationService = Depends(get_tenant_application_service),
    db: Session = Depends(get_db)
):
    """创建新租户"""
    try:
        # 权限检查：只有系统管理员可以创建租户
        if not await tenant_service.is_user_admin(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足：需要系统管理员权限"
            )
        
        tenant = await tenant_service.create_tenant_use_case(
            name=tenant_data.name,
            display_name=tenant_data.display_name,
            description=tenant_data.description,
            tenant_type=tenant_data.tenant_type,
            contact_name=tenant_data.contact_name,
            contact_email=tenant_data.contact_email,
            contact_phone=tenant_data.contact_phone
        )
        
        return tenant
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
    db: Session = Depends(get_db)
):
    """更新租户信息"""
    try:
        # 权限检查：系统管理员或租户管理员
        if not await tenant_service.is_user_admin(current_user.id):
            if current_user.tenant_id != tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足：只能更新自己租户的信息"
                )
        
        tenant = await tenant_service.update_tenant_use_case(
            tenant_id=tenant_id,
            display_name=tenant_data.display_name,
            description=tenant_data.description,
            contact_name=tenant_data.contact_name,
            contact_email=tenant_data.contact_email,
            contact_phone=tenant_data.contact_phone
        )
        
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="租户不存在"
            )
        
        return tenant
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
    db: Session = Depends(get_db)
):
    """删除租户"""
    try:
        # 权限检查：只有系统管理员可以删除租户
        if not await tenant_service.is_user_admin(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足：需要系统管理员权限"
            )
        
        success = await tenant_service.delete_tenant_use_case(tenant_id)
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
    db: Session = Depends(get_db)
):
    """激活租户"""
    try:
        # 权限检查：只有系统管理员可以激活租户
        if not await tenant_service.is_user_admin(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足：需要系统管理员权限"
            )
        
        success = await tenant_service.activate_tenant_use_case(tenant_id)
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
    db: Session = Depends(get_db)
):
    """停用租户"""
    try:
        # 权限检查：只有系统管理员可以停用租户
        if not await tenant_service.is_user_admin(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足：需要系统管理员权限"
            )
        
        success = await tenant_service.deactivate_tenant_use_case(tenant_id)
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
    db: Session = Depends(get_db)
):
    """获取租户统计信息"""
    try:
        # 权限检查：系统管理员或租户管理员
        if not await tenant_service.is_user_admin(current_user.id):
            if current_user.tenant_id != tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足：只能查看自己租户的统计信息"
                )
        
        statistics = await tenant_service.get_tenant_statistics_use_case(tenant_id)
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
