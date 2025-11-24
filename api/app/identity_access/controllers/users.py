import logging
from fastapi import APIRouter, Depends, Query, status
from typing import List, Optional

from app.identity_access.schemas.user import UserCreate, UserUpdate, UserResponse, RoleResponse, UserListResponse
from app.identity_access.models.user import User
from app.identity_access.enums import UserStatus
from app.identity_access.services.user_service import UserService
from app.identity_access.services.role_service import RoleService
from app.identity_access.deps.user_deps import get_user_service, get_role_service
from app.identity_access.deps.auth_deps import get_current_user, require_role
from app.identity_access.schemas.user_permission_schemas import (
    UserPermissionCheckResponse, UserRoleCheckResponse,
    UserPermissionSummaryResponse, UserPermissionsResponse, UserRolesResponse
)
from app.core.api import ApiResponse, BusinessException, ErrorCode, SystemException

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # 确保调试日志能够输出
router = APIRouter()

def _handle_unexpected_error(message: str, exc: Exception) -> SystemException:
    return SystemException(message=message, code=ErrorCode.SYSTEM_ERROR)

@router.post("", response_model=ApiResponse[UserResponse], status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    current_user: User = Depends(require_role("administrator")), # 简化权限检查
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse[UserResponse]:
    """创建新用户"""
    try:
        logger.info(f"开始创建用户: username={user_in.username}, email={user_in.email}, roles={user_in.roles}")
        logger.info(f"用户输入数据: {user_in.model_dump(exclude={'password'})}")
        
        user = await user_service.create_user(user_in)
        logger.info(f"用户创建成功: user_id={user.id}, username={user.username}")
        
        # 转换用户为 UserResponse 格式
        roles = [role.name for role in user.roles] if user.roles else []
        active_role = roles[0] if roles else None
        
        user_data = {
            "id": user.id,
            "tenant_id": user.tenant_id,
            "email": user.email,
            "username": user.username,
            "phone": user.phone,
            "avatar": user.avatar,
            "is_active": user.status == UserStatus.ACTIVE if hasattr(user, 'status') else getattr(user, 'is_active', True),
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "last_login_at": getattr(user, 'last_login_at', None),
            "roles": roles,
            "active_role": active_role,
            "extended_info": None
        }
        
        user_response = UserResponse(**user_data)
        logger.info(f"用户响应对象创建成功: user_id={user_response.id}")
        
        return ApiResponse.success(user_response, message="创建用户成功")
    except BusinessException as be:
        logger.warning(f"业务异常: {be.message}, code={be.code}")
        raise
    except Exception as e:
        logger.error(f"创建用户失败: error={str(e)}", exc_info=True)
        raise _handle_unexpected_error("创建用户失败", e)

@router.get("", response_model=ApiResponse[UserListResponse])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(require_role("administrator")),
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse[UserListResponse]:
    """获取用户列表"""
    try:
        logger.info(f"开始获取用户列表: skip={skip}, limit={limit}, search={search}, current_user_id={current_user.id}")
        
        logger.info("调用 user_service.get_users_list...")
        users = await user_service.get_users_list(skip=skip, limit=limit, search=search)
        logger.info(f"获取到 {len(users) if users else 0} 个用户")
        logger.info(f"users 类型: {type(users)}, 是否为列表: {isinstance(users, list)}")
        
        logger.info("调用 user_service.count_users...")
        total = await user_service.count_users(search=search)
        logger.info(f"用户总数: {total}")
        
        # 转换用户列表为 UserResponse
        logger.info("开始转换用户列表...")
        user_responses = []
        if not users:
            logger.warning("users 为空或 None")
        for idx, user in enumerate(users):
            try:
                logger.info(f"处理用户 {idx+1}/{len(users)}: user_id={user.id}, username={user.username}")
                
                # 将 Role 对象列表转换为角色名称字符串列表
                roles = [role.name for role in user.roles] if user.roles else []
                logger.info(f"用户 {user.id} 的角色: {roles}")
                
                # 获取活跃角色
                active_role = None
                if hasattr(user, '_active_role') and user._active_role:
                    active_role = user._active_role
                elif roles:
                    active_role = roles[0]
                
                # 构建 UserResponse 数据
                # 处理 is_active 字段，从status转换为布尔值
                is_active_value = user.status == UserStatus.ACTIVE if hasattr(user, 'status') else getattr(user, 'is_active', True)
                
                user_data = {
                    "id": user.id,
                    "tenant_id": user.tenant_id,
                    "email": user.email,
                    "username": user.username,
                    "phone": user.phone,
                    "avatar": user.avatar,
                    "is_active": is_active_value,
                    "created_at": user.created_at,
                    "updated_at": user.updated_at,
                    "last_login_at": getattr(user, 'last_login_at', None),
                    "roles": roles,
                    "active_role": active_role,
                    "extended_info": None
                }
                
                logger.info(f"用户 {user.id} 的 status 值: {user.status}")
                logger.info(f"处理后的 is_active 值: {is_active_value} (类型: {type(is_active_value)})")
                
                user_response = UserResponse(**user_data)
                user_responses.append(user_response)
                logger.info(f"用户 {user.id} 转换成功")
            except Exception as user_error:
                logger.error(f"转换用户失败: user_id={user.id if user else 'unknown'}, error={str(user_error)}", exc_info=True)
                raise
        
        logger.info(f"成功转换 {len(user_responses)} 个用户")
        
        # 确保 users 是列表
        if not isinstance(user_responses, list):
            logger.warning(f"user_responses 不是列表类型: {type(user_responses)}")
            user_responses = list(user_responses) if user_responses else []
        
        logger.info(f"准备构建 UserListResponse: user_responses数量={len(user_responses)}, total={total}")
        response = UserListResponse(
            users=user_responses,
            total=total,
            skip=skip,
            limit=limit
        )
        
        logger.info(f"构建响应对象: users数量={len(response.users)}, total={response.total}")
        logger.info(f"响应对象类型: {type(response)}, users类型: {type(response.users)}")
        logger.info(f"response.users 是否为列表: {isinstance(response.users, list)}")
        
        api_response = ApiResponse.success(response, message="获取用户列表成功")
        logger.info(f"API响应: code={api_response.code}, data类型={type(api_response.data)}")
        if api_response.data:
            logger.info(f"API响应data内容: users数量={len(api_response.data.users) if hasattr(api_response.data, 'users') else 'N/A'}")
            logger.info(f"API响应data.users 是否为列表: {isinstance(api_response.data.users, list) if hasattr(api_response.data, 'users') else 'N/A'}")
        
        # 序列化检查
        import json
        try:
            serialized = api_response.model_dump()
            logger.info(f"序列化后的数据结构: data类型={type(serialized.get('data'))}")
            if serialized.get('data'):
                logger.info(f"序列化后data.users类型: {type(serialized['data'].get('users'))}")
                logger.info(f"序列化后data.users是否为列表: {isinstance(serialized['data'].get('users'), list)}")
        except Exception as ser_error:
            logger.error(f"序列化检查失败: {ser_error}")
        
        return api_response
    except Exception as e:
        logger.error(f"获取用户列表失败: skip={skip}, limit={limit}, search={search}, error={str(e)}", exc_info=True)
        raise _handle_unexpected_error("获取用户列表失败", e)

@router.get("/me", response_model=ApiResponse[UserResponse])
async def read_user_me(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse[UserResponse]:
    """获取当前用户信息"""
    # 将 Role 对象列表转换为角色名称字符串列表
    roles = [role.name for role in current_user.roles] if current_user.roles else []
    
    # 获取活跃角色（从 JWT token 中获取，或使用默认角色）
    active_role = None
    if hasattr(current_user, '_active_role') and current_user._active_role:
        active_role = current_user._active_role
    else:
        # 尝试从用户服务获取默认角色
        try:
            active_role = await user_service.get_user_default_role(current_user.id)
        except:
            pass
        if not active_role and roles:
            active_role = roles[0]

    # 获取权限列表（从所有角色中收集）
    permissions = []
    for role in current_user.roles:
        if role.permissions:
            for perm in role.permissions:
                if perm.code not in permissions:
                    permissions.append(perm.code)
    
    # 构建 UserResponse 数据
    user_data = {
        "id": current_user.id,
        "tenant_id": current_user.tenant_id,
        "email": current_user.email,
        "username": current_user.username,
        "phone": current_user.phone,
        "avatar": current_user.avatar,
        "is_active": current_user.status == UserStatus.ACTIVE,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at,
        "last_login_at": getattr(current_user, 'last_login_at', None),
        "roles": roles,
        "permissions": permissions,
        "active_role": active_role,
        "extended_info": None  # 可以后续扩展
    }
    
    user_response = UserResponse(**user_data)
    return ApiResponse.success(user_response, message="获取当前用户成功")

@router.put("/me", response_model=ApiResponse[UserResponse])
async def update_user_me(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse[UserResponse]:
    """更新当前用户信息"""
    try:
        # 禁止更新角色
        if hasattr(user_in, "roles"):
            user_in.roles = None
        
        user = await user_service.update_user(current_user.id, user_in)
        return ApiResponse.success(user, message="更新当前用户成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("更新用户信息失败", e)

@router.get("/{user_id}", response_model=ApiResponse[UserResponse])
async def read_user_by_id(
    user_id: str,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse[UserResponse]:
    """根据ID获取用户信息"""
    try:
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise BusinessException("用户不存在", code=ErrorCode.NOT_FOUND, status_code=status.HTTP_404_NOT_FOUND)
        return ApiResponse.success(user, message="获取用户成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("获取用户信息失败", e)

@router.put("/{user_id}", response_model=ApiResponse[UserResponse])
async def update_user(
    user_id: str,
    user_in: UserUpdate,
    current_user: User = Depends(require_role("administrator")),
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse[UserResponse]:
    """更新用户信息 (管理员)"""
    try:
        logger.info(f"开始更新用户: user_id={user_id}, current_user_id={current_user.id}")
        logger.info(f"更新数据: {user_in.model_dump(exclude_unset=True)}")
        user = await user_service.update_user(user_id, user_in)
        logger.info(f"用户更新成功: user_id={user.id}, username={user.username}, status={user.status}")
        
        # 转换用户为 UserResponse 格式
        roles = [role.name for role in user.roles] if user.roles else []
        active_role = roles[0] if roles else None
        
        user_data = {
            "id": user.id,
            "tenant_id": user.tenant_id,
            "email": user.email,
            "username": user.username,
            "phone": user.phone,
            "avatar": user.avatar,
            "is_active": user.status == UserStatus.ACTIVE if hasattr(user, 'status') else getattr(user, 'is_active', True),
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "last_login_at": getattr(user, 'last_login_at', None),
            "roles": roles,
            "active_role": active_role,
            "extended_info": None
        }
        
        user_response = UserResponse(**user_data)
        logger.info(f"用户响应对象创建成功: user_id={user_response.id}")
        
        return ApiResponse.success(user_response, message="更新用户成功")
    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"更新用户失败: error={str(e)}", exc_info=True)
        raise _handle_unexpected_error("更新用户信息失败", e)

@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_role("administrator")),
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse[dict]:
    """删除用户（物理删除）"""
    try:
        logger.info(f"开始删除用户: user_id={user_id}, current_user_id={current_user.id}")
        
        # 防止删除自己
        if user_id == current_user.id:
            raise BusinessException("不能删除自己的账户", code=ErrorCode.BAD_REQUEST, status_code=status.HTTP_400_BAD_REQUEST)
        
        success = await user_service.delete_user(user_id)
        if not success:
            raise BusinessException("用户不存在", code=ErrorCode.NOT_FOUND, status_code=status.HTTP_404_NOT_FOUND)
        
        logger.info(f"用户删除成功: user_id={user_id}")
        return ApiResponse.success({}, message="删除用户成功")
    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"删除用户失败: error={str(e)}", exc_info=True)
        raise _handle_unexpected_error("删除用户失败", e)

@router.get("/roles/all", response_model=ApiResponse[List[RoleResponse]])
async def read_roles(
    current_user: User = Depends(require_role("administrator")),
    role_service: RoleService = Depends(get_role_service)
) -> ApiResponse[List[RoleResponse]]:
    """获取所有角色"""
    try:
        roles = role_service.get_all_roles()
        return ApiResponse.success(roles, message="获取角色列表成功")
    except Exception as e:
        raise _handle_unexpected_error("获取角色列表失败", e)

# ==================== 权限相关 ====================

@router.get("/{user_id}/permissions/check", response_model=ApiResponse[UserPermissionCheckResponse])
async def check_user_permission(
    user_id: str,
    permission: str = Query(..., description="要检查的权限代码"),
    current_user: User = Depends(get_current_user),
    role_service: RoleService = Depends(get_role_service)
) -> ApiResponse[UserPermissionCheckResponse]:
    """检查用户是否有指定权限"""
    try:
        has_permission = await role_service.check_permission(user_id, permission)
        return ApiResponse.success(UserPermissionCheckResponse(
            user_id=user_id,
            permission=permission,
            has_permission=has_permission
        ))
    except Exception as e:
        raise _handle_unexpected_error("检查用户权限失败", e)

@router.get("/{user_id}/roles/check", response_model=ApiResponse[UserRoleCheckResponse])
async def check_user_role(
    user_id: str,
    role: str = Query(..., description="要检查的角色名称"),
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse[UserRoleCheckResponse]:
    """检查用户是否有指定角色"""
    try:
        user = await user_service.get_user_by_id(user_id)
        has_role = False
        if user:
            has_role = any(r.name == role for r in user.roles)
            
        return ApiResponse.success(UserRoleCheckResponse(
            user_id=user_id,
            role=role,
            has_role=has_role
        ))
    except Exception as e:
        raise _handle_unexpected_error("检查用户角色失败", e)

@router.get("/{user_id}/roles", response_model=ApiResponse[UserRolesResponse])
async def get_user_roles(
    user_id: str,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse[UserRolesResponse]:
    """获取用户角色列表"""
    try:
        user = await user_service.get_user_by_id(user_id)
        roles = [r.name for r in user.roles] if user else []
        return ApiResponse.success(UserRolesResponse(
            user_id=user_id,
            roles=roles
        ))
    except Exception as e:
        raise _handle_unexpected_error("获取用户角色列表失败", e)

@router.get("/{user_id}/permissions/summary", response_model=ApiResponse[UserPermissionSummaryResponse])
async def get_user_permissions_summary(
    user_id: str,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    role_service: RoleService = Depends(get_role_service)
) -> ApiResponse[UserPermissionSummaryResponse]:
    """获取用户权限摘要"""
    try:
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise BusinessException("用户不存在", code=ErrorCode.NOT_FOUND, status_code=status.HTTP_404_NOT_FOUND)
        
        # 获取角色列表
        roles = [r.name for r in user.roles] if user.roles else []
        
        # 获取权限列表（从所有角色中收集）
        permissions = []
        is_admin = False
        for role in user.roles:
            if role.is_admin or role.name in ["administrator", "super_admin"]:
                is_admin = True
            # 收集角色的权限
            if role.permissions:
                for perm in role.permissions:
                    if perm.code not in permissions:
                        permissions.append(perm.code)
        
        # 获取租户信息
        tenant_id = user.tenant_id
        tenant_name = None
        if user.tenant:
            tenant_name = user.tenant.name
        
        summary = UserPermissionSummaryResponse(
            user_id=user.id,
            username=user.username,
            roles=roles,
            permissions=permissions,
            is_admin=is_admin,
            tenant_id=tenant_id,
            tenant_name=tenant_name,
            last_login_at=getattr(user, 'last_login_at', None),
            created_at=user.created_at
        )
        
        return ApiResponse.success(summary, message="获取用户权限摘要成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("获取用户权限摘要失败", e)

