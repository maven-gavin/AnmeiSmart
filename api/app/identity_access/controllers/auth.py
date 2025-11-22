import logging
from typing import List
from fastapi import APIRouter, Depends, status, Body
from fastapi.security import OAuth2PasswordRequestForm

from app.identity_access.schemas.token import Token, RefreshTokenRequest
from app.identity_access.schemas.user import UserResponse, RoleResponse
from app.identity_access.models.user import User
from app.identity_access.services.auth_service import AuthService
from app.identity_access.deps.user_deps import get_auth_service
from app.identity_access.deps.auth_deps import get_current_user
from app.core.api import ApiResponse, BusinessException, ErrorCode, SystemException

logger = logging.getLogger(__name__)
router = APIRouter()

def _handle_unexpected_error(message: str, exc: Exception) -> SystemException:
    return SystemException(message=message, code=ErrorCode.SYSTEM_ERROR)

@router.post("/login", response_model=ApiResponse[Token])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
) -> ApiResponse[Token]:
    """
    用户登录
    """
    try:
        # 获取IP和User-Agent通常在Request对象中，这里为了简单暂不获取或需要修改Controller签名引入Request
        # 为了保持Service接口，这里传入None
        token = await auth_service.login(
            username_or_email=form_data.username,
            password=form_data.password
        )
        return ApiResponse.success(token, message="登录成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("登录失败", e)

@router.post("/refresh-token", response_model=ApiResponse[Token])
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> ApiResponse[Token]:
    """
    刷新令牌
    """
    try:
        token = await auth_service.refresh_token(refresh_request.token)
        return ApiResponse.success(token, message="令牌刷新成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("令牌刷新失败", e)

@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> ApiResponse[UserResponse]:
    """
    获取当前用户信息
    """
    # 将 Role 对象列表转换为角色名称字符串列表
    roles = [role.name for role in current_user.roles] if current_user.roles else []
    
    # 获取活跃角色（从 JWT token 中获取，或使用默认角色）
    active_role = None
    if hasattr(current_user, '_active_role') and current_user._active_role:
        active_role = current_user._active_role
    elif roles:
        active_role = roles[0]
    
    # 构建 UserResponse 数据
    user_data = {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "phone": current_user.phone,
        "avatar": current_user.avatar,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at,
        "last_login_at": getattr(current_user, 'last_login_at', None),
        "roles": roles,
        "active_role": active_role,
        "extended_info": None  # 可以后续扩展
    }
    
    user_response = UserResponse(**user_data)
    return ApiResponse.success(user_response, message="获取当前用户成功")

@router.post("/logout", response_model=ApiResponse[bool])
async def logout(
    current_user: User = Depends(get_current_user)
) -> ApiResponse[bool]:
    """
    用户登出
    目前JWT是无状态的，登出通常由前端丢弃Token实现。
    后端可以是黑名单机制，这里暂时返回True。
    """
    return ApiResponse.success(True, message="登出成功")

@router.get("/roles/details", response_model=ApiResponse[List[RoleResponse]])
async def get_current_user_roles_details(
    current_user: User = Depends(get_current_user)
) -> ApiResponse[List[RoleResponse]]:
    """
    获取当前用户的角色详情列表
    """
    try:
        logger.debug(f"开始获取用户角色详情: user_id={current_user.id}, username={current_user.username}")
        
        # 检查用户是否有角色
        if not current_user.roles:
            logger.debug(f"用户 {current_user.id} 没有角色")
            return ApiResponse.success([], message="获取角色详情成功")
        
        logger.debug(f"用户 {current_user.id} 有 {len(current_user.roles)} 个角色")
        
        # 使用 model_validate 从 ORM 对象转换，因为 RoleResponse 配置了 from_attributes=True
        roles = []
        for idx, role in enumerate(current_user.roles):
            try:
                logger.debug(f"处理角色 {idx+1}/{len(current_user.roles)}: role_id={role.id}, name={role.name}")
                logger.debug(f"角色属性: display_name={role.display_name}, is_active={role.is_active}, is_system={role.is_system}, is_admin={role.is_admin}")
                logger.debug(f"角色属性: priority={role.priority}, tenant_id={role.tenant_id}")
                logger.debug(f"角色属性: created_at={role.created_at}, updated_at={role.updated_at}")
                
                role_response = RoleResponse.model_validate(role)
                logger.debug(f"角色转换成功: {role_response.model_dump()}")
                roles.append(role_response)
            except Exception as role_error:
                logger.error(f"转换角色失败: role_id={role.id}, error={str(role_error)}", exc_info=True)
                raise
        
        logger.debug(f"成功转换 {len(roles)} 个角色")
        return ApiResponse.success(roles, message="获取角色详情成功")
    except Exception as e:
        logger.error(f"获取角色详情失败: user_id={current_user.id if current_user else 'unknown'}, error={str(e)}", exc_info=True)
        raise _handle_unexpected_error("获取角色详情失败", e)

@router.post("/switch-role", response_model=ApiResponse[Token])
async def switch_role(
    role: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> ApiResponse[Token]:
    """
    切换当前活跃角色
    """
    try:
        token = await auth_service.switch_role(current_user.id, role)
        return ApiResponse.success(token, message="角色切换成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("角色切换失败", e)

