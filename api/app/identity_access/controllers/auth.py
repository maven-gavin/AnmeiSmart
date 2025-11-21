from fastapi import APIRouter, Depends, status, Body
from fastapi.security import OAuth2PasswordRequestForm

from app.identity_access.schemas.token import Token, RefreshTokenRequest
from app.identity_access.models.user import User
from app.identity_access.services.auth_service import AuthService
from app.identity_access.deps.user_deps import get_auth_service
from app.identity_access.deps.auth_deps import get_current_user
from app.core.api import ApiResponse, BusinessException, ErrorCode, SystemException

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

