from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status

from app.identity_access.schemas.user import RoleCreate, RoleUpdate, RoleResponse
from app.identity_access.models.user import User, Role
from app.identity_access.services.role_service import RoleService
from app.identity_access.deps.user_deps import get_role_service
from app.identity_access.deps.auth_deps import get_current_user, require_role
from app.core.api import ApiResponse, BusinessException, ErrorCode, SystemException

router = APIRouter()

def _handle_unexpected_error(message: str, exc: Exception) -> SystemException:
    return SystemException(message=message, code=ErrorCode.SYSTEM_ERROR)

def _convert_role_to_response(role: Role) -> RoleResponse:
    """将 Role 模型转换为 RoleResponse"""
    # 获取租户名称
    tenant_name = None
    if role.tenant:
        tenant_name = role.tenant.display_name or role.tenant.name
    
    return RoleResponse(
        id=role.id,
        name=role.name,
        display_name=role.display_name,
        description=role.description,
        tenant_id=role.tenant_id,
        tenant_name=tenant_name,
        is_active=role.is_active if role.is_active is not None else True,
        is_system=role.is_system if role.is_system is not None else False,
        is_admin=role.is_admin if role.is_admin is not None else False,
        priority=role.priority if role.priority is not None else 0,
        created_at=role.created_at if hasattr(role, 'created_at') else None,
        updated_at=role.updated_at if hasattr(role, 'updated_at') else None,
    )

@router.get("", response_model=ApiResponse[List[RoleResponse]])
async def list_roles(
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(require_role("administrator")),
    role_service: RoleService = Depends(get_role_service)
) -> ApiResponse[List[RoleResponse]]:
    """获取角色列表"""
    try:
        roles = role_service.get_all_roles(search=search)
        role_responses = [_convert_role_to_response(role) for role in roles]
        return ApiResponse.success(role_responses, message="获取角色列表成功")
    except Exception as e:
        raise _handle_unexpected_error("获取角色列表失败", e)

@router.post("", response_model=ApiResponse[RoleResponse], status_code=status.HTTP_201_CREATED)
async def create_role(
    role_in: RoleCreate,
    current_user: User = Depends(require_role("administrator")),
    role_service: RoleService = Depends(get_role_service)
) -> ApiResponse[RoleResponse]:
    """创建新角色"""
    try:
        role = role_service.create_role(role_in)
        # 重新加载以获取租户信息
        role = role_service.get_role_by_id(role.id)
        role_response = _convert_role_to_response(role)
        return ApiResponse.success(role_response, message="创建角色成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("创建角色失败", e)

@router.get("/{role_id}", response_model=ApiResponse[RoleResponse])
async def get_role(
    role_id: str,
    current_user: User = Depends(require_role("administrator")),
    role_service: RoleService = Depends(get_role_service)
) -> ApiResponse[RoleResponse]:
    """获取角色详情"""
    try:
        role = role_service.get_role_by_id(role_id)
        if not role:
            raise BusinessException("角色不存在", code=ErrorCode.NOT_FOUND, status_code=status.HTTP_404_NOT_FOUND)
        role_response = _convert_role_to_response(role)
        return ApiResponse.success(role_response, message="获取角色成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("获取角色详情失败", e)

@router.put("/{role_id}", response_model=ApiResponse[RoleResponse])
async def update_role(
    role_id: str,
    role_in: RoleUpdate,
    current_user: User = Depends(require_role("administrator")),
    role_service: RoleService = Depends(get_role_service)
) -> ApiResponse[RoleResponse]:
    """更新角色"""
    try:
        role = role_service.update_role(role_id, role_in)
        # 重新加载以获取租户信息
        role = role_service.get_role_by_id(role_id)
        role_response = _convert_role_to_response(role)
        return ApiResponse.success(role_response, message="更新角色成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("更新角色失败", e)

@router.delete("/{role_id}", response_model=ApiResponse[bool])
async def delete_role(
    role_id: str,
    current_user: User = Depends(require_role("administrator")),
    role_service: RoleService = Depends(get_role_service)
) -> ApiResponse[bool]:
    """删除角色"""
    try:
        success = role_service.delete_role(role_id)
        return ApiResponse.success(success, message="删除角色成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("删除角色失败", e)
