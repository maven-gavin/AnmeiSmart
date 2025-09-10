"""
权限管理API端点

提供权限的CRUD操作和角色权限关联管理功能。
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.common.infrastructure.db.base import get_db
from app.identity_access.deps.auth_deps import get_current_user
from app.identity_access.infrastructure.db.user import User
from app.identity_access.application.role_permission_application_service import RolePermissionApplicationService
from app.identity_access.deps.auth_deps import get_role_permission_application_service
from app.identity_access.schemas.permission_schemas import (
    PermissionCreate, PermissionUpdate, PermissionResponse, PermissionListResponse,
    RolePermissionAssign, RolePermissionResponse
)

router = APIRouter(prefix="/permissions", tags=["权限管理"])


@router.get("/", response_model=PermissionListResponse)
async def list_permissions(
    tenant_id: Optional[str] = Query(None, description="租户ID筛选"),
    permission_type: Optional[str] = Query(None, description="权限类型筛选"),
    scope: Optional[str] = Query(None, description="权限范围筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    current_user: User = Depends(get_current_user),
    permission_service: RolePermissionApplicationService = Depends(get_role_permission_application_service),
    db: Session = Depends(get_db)
):
    """获取权限列表"""
    try:
        # 权限检查：系统管理员或租户管理员
        if not await permission_service.is_user_admin(current_user.id):
            # 非管理员只能查看自己租户的权限
            if tenant_id and tenant_id != current_user.tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足：只能查看自己租户的权限"
                )
            tenant_id = current_user.tenant_id
        
        permissions = await permission_service.list_permissions_use_case(
            tenant_id=tenant_id,
            permission_type=permission_type,
            scope=scope,
            is_active=is_active,
            skip=skip,
            limit=limit
        )
        
        return PermissionListResponse(
            permissions=permissions,
            total=len(permissions),
            skip=skip,
            limit=limit
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取权限列表失败: {str(e)}"
        )


@router.get("/{permission_id}", response_model=PermissionResponse)
async def get_permission(
    permission_id: str,
    current_user: User = Depends(get_current_user),
    permission_service: RolePermissionApplicationService = Depends(get_role_permission_application_service),
    db: Session = Depends(get_db)
):
    """获取权限详情"""
    try:
        permission = await permission_service.get_permission_use_case(permission_id)
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="权限不存在"
            )
        
        # 权限检查：系统管理员或租户管理员
        if not await permission_service.is_user_admin(current_user.id):
            if permission.tenant_id != current_user.tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足：只能查看自己租户的权限"
                )
        
        return permission
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取权限详情失败: {str(e)}"
        )


@router.post("/", response_model=PermissionResponse)
async def create_permission(
    permission_data: PermissionCreate,
    current_user: User = Depends(get_current_user),
    permission_service: RolePermissionApplicationService = Depends(get_role_permission_application_service),
    db: Session = Depends(get_db)
):
    """创建新权限"""
    try:
        # 权限检查：系统管理员或租户管理员
        if not await permission_service.is_user_admin(current_user.id):
            if permission_data.tenant_id != current_user.tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足：只能为自己租户创建权限"
                )
        
        permission = await permission_service.create_permission_use_case(
            name=permission_data.name,
            display_name=permission_data.display_name,
            description=permission_data.description,
            permission_type=permission_data.permission_type,
            scope=permission_data.scope,
            resource=permission_data.resource,
            action=permission_data.action,
            tenant_id=permission_data.tenant_id or current_user.tenant_id
        )
        
        return permission
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建权限失败: {str(e)}"
        )


@router.put("/{permission_id}", response_model=PermissionResponse)
async def update_permission(
    permission_id: str,
    permission_data: PermissionUpdate,
    current_user: User = Depends(get_current_user),
    permission_service: RolePermissionApplicationService = Depends(get_role_permission_application_service),
    db: Session = Depends(get_db)
):
    """更新权限信息"""
    try:
        # 先获取权限信息进行权限检查
        existing_permission = await permission_service.get_permission_use_case(permission_id)
        if not existing_permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="权限不存在"
            )
        
        # 权限检查：系统管理员或租户管理员
        if not await permission_service.is_user_admin(current_user.id):
            if existing_permission.tenant_id != current_user.tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足：只能更新自己租户的权限"
                )
        
        permission = await permission_service.update_permission_use_case(
            permission_id=permission_id,
            display_name=permission_data.display_name,
            description=permission_data.description,
            resource=permission_data.resource,
            action=permission_data.action
        )
        
        return permission
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
            detail=f"更新权限失败: {str(e)}"
        )


@router.delete("/{permission_id}")
async def delete_permission(
    permission_id: str,
    current_user: User = Depends(get_current_user),
    permission_service: RolePermissionApplicationService = Depends(get_role_permission_application_service),
    db: Session = Depends(get_db)
):
    """删除权限"""
    try:
        # 先获取权限信息进行权限检查
        existing_permission = await permission_service.get_permission_use_case(permission_id)
        if not existing_permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="权限不存在"
            )
        
        # 权限检查：系统管理员或租户管理员
        if not await permission_service.is_user_admin(current_user.id):
            if existing_permission.tenant_id != current_user.tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足：只能删除自己租户的权限"
                )
        
        success = await permission_service.delete_permission_use_case(permission_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="权限不存在"
            )
        
        return {"message": "权限删除成功"}
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
            detail=f"删除权限失败: {str(e)}"
        )


@router.post("/{permission_id}/roles/{role_id}")
async def assign_permission_to_role(
    permission_id: str,
    role_id: str,
    current_user: User = Depends(get_current_user),
    permission_service: RolePermissionApplicationService = Depends(get_role_permission_application_service),
    db: Session = Depends(get_db)
):
    """为角色分配权限"""
    try:
        # 权限检查：系统管理员或租户管理员
        if not await permission_service.is_user_admin(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足：需要管理员权限"
            )
        
        success = await permission_service.assign_permission_to_role_use_case(
            role_id=role_id,
            permission_id=permission_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="分配权限失败：角色或权限不存在"
            )
        
        return {"message": "权限分配成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分配权限失败: {str(e)}"
        )


@router.delete("/{permission_id}/roles/{role_id}")
async def remove_permission_from_role(
    permission_id: str,
    role_id: str,
    current_user: User = Depends(get_current_user),
    permission_service: RolePermissionApplicationService = Depends(get_role_permission_application_service),
    db: Session = Depends(get_db)
):
    """从角色移除权限"""
    try:
        # 权限检查：系统管理员或租户管理员
        if not await permission_service.is_user_admin(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足：需要管理员权限"
            )
        
        success = await permission_service.remove_permission_from_role_use_case(
            role_id=role_id,
            permission_id=permission_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="移除权限失败：角色或权限不存在"
            )
        
        return {"message": "权限移除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"移除权限失败: {str(e)}"
        )


@router.get("/{permission_id}/roles", response_model=List[RolePermissionResponse])
async def get_permission_roles(
    permission_id: str,
    current_user: User = Depends(get_current_user),
    permission_service: RolePermissionApplicationService = Depends(get_role_permission_application_service),
    db: Session = Depends(get_db)
):
    """获取拥有指定权限的角色列表"""
    try:
        # 先检查权限是否存在
        permission = await permission_service.get_permission_use_case(permission_id)
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="权限不存在"
            )
        
        # 权限检查：系统管理员或租户管理员
        if not await permission_service.is_user_admin(current_user.id):
            if permission.tenant_id != current_user.tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足：只能查看自己租户的权限角色"
                )
        
        roles = await permission_service.get_permission_roles_use_case(permission_id)
        return roles
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取权限角色失败: {str(e)}"
        )
