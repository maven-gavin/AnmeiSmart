"""
用户权限检查API端点

提供用户权限和角色检查功能。
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.common.infrastructure.db.base import get_db
from app.identity_access.deps.auth_deps import get_current_user
from app.identity_access.infrastructure.db.user import User
from app.identity_access.application.identity_access_application_service import IdentityAccessApplicationService
from app.identity_access.deps.auth_deps import get_identity_access_application_service
from app.identity_access.schemas.user_permission_schemas import (
    UserPermissionCheckResponse, UserRoleCheckResponse, 
    UserPermissionSummaryResponse, UserPermissionsResponse, UserRolesResponse
)

router = APIRouter(prefix="/users", tags=["用户权限"])


@router.get("/{user_id}/permissions/check", response_model=UserPermissionCheckResponse)
async def check_user_permission(
    user_id: str,
    permission: str = Query(..., description="要检查的权限名称"),
    current_user: User = Depends(get_current_user),
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service),
    db: Session = Depends(get_db)
):
    """检查用户是否有指定权限"""
    try:
        # 权限检查：只能检查自己的权限，或管理员可以检查任何用户
        if current_user.id != user_id:
            if not await identity_service.is_user_admin_use_case(current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足：只能检查自己的权限"
                )
        
        has_permission = await identity_service.check_user_permission_use_case(user_id, permission)
        
        return UserPermissionCheckResponse(
            user_id=user_id,
            permission=permission,
            has_permission=has_permission
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检查用户权限失败: {str(e)}"
        )


@router.get("/{user_id}/roles/check", response_model=UserRoleCheckResponse)
async def check_user_role(
    user_id: str,
    role: str = Query(..., description="要检查的角色名称"),
    current_user: User = Depends(get_current_user),
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service),
    db: Session = Depends(get_db)
):
    """检查用户是否有指定角色"""
    try:
        # 权限检查：只能检查自己的角色，或管理员可以检查任何用户
        if current_user.id != user_id:
            if not await identity_service.is_user_admin_use_case(current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足：只能检查自己的角色"
                )
        
        has_role = await identity_service.check_user_role_use_case(user_id, role)
        
        return UserRoleCheckResponse(
            user_id=user_id,
            role=role,
            has_role=has_role
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检查用户角色失败: {str(e)}"
        )


@router.get("/{user_id}/admin/check", response_model=dict)
async def check_user_admin(
    user_id: str,
    current_user: User = Depends(get_current_user),
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service),
    db: Session = Depends(get_db)
):
    """检查用户是否为管理员"""
    try:
        # 权限检查：只能检查自己的管理员状态，或管理员可以检查任何用户
        if current_user.id != user_id:
            if not await identity_service.is_user_admin_use_case(current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足：只能检查自己的管理员状态"
                )
        
        is_admin = await identity_service.is_user_admin_use_case(user_id)
        
        return {
            "user_id": user_id,
            "is_admin": is_admin
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检查用户管理员状态失败: {str(e)}"
        )


@router.get("/{user_id}/permissions", response_model=UserPermissionsResponse)
async def get_user_permissions(
    user_id: str,
    current_user: User = Depends(get_current_user),
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service),
    db: Session = Depends(get_db)
):
    """获取用户权限列表"""
    try:
        # 权限检查：只能查看自己的权限，或管理员可以查看任何用户
        if current_user.id != user_id:
            if not await identity_service.is_user_admin_use_case(current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足：只能查看自己的权限"
                )
        
        permissions = await identity_service.get_user_permissions_use_case(user_id)
        
        return UserPermissionsResponse(
            user_id=user_id,
            permissions=permissions
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户权限列表失败: {str(e)}"
        )


@router.get("/{user_id}/roles", response_model=UserRolesResponse)
async def get_user_roles(
    user_id: str,
    current_user: User = Depends(get_current_user),
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service),
    db: Session = Depends(get_db)
):
    """获取用户角色列表"""
    try:
        # 权限检查：只能查看自己的角色，或管理员可以查看任何用户
        if current_user.id != user_id:
            if not await identity_service.is_user_admin_use_case(current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足：只能查看自己的角色"
                )
        
        roles = await identity_service.get_user_roles_use_case(user_id)
        
        return UserRolesResponse(
            user_id=user_id,
            roles=roles
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户角色列表失败: {str(e)}"
        )


@router.get("/{user_id}/permissions/summary", response_model=UserPermissionSummaryResponse)
async def get_user_permission_summary(
    user_id: str,
    current_user: User = Depends(get_current_user),
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service),
    db: Session = Depends(get_db)
):
    """获取用户权限摘要"""
    try:
        # 权限检查：只能查看自己的权限摘要，或管理员可以查看任何用户
        if current_user.id != user_id:
            if not await identity_service.is_user_admin_use_case(current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足：只能查看自己的权限摘要"
                )
        
        summary = await identity_service.get_user_permission_summary_use_case(user_id)
        
        return summary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户权限摘要失败: {str(e)}"
        )
