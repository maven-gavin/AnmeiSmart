from typing import List
from fastapi import APIRouter, Depends, status, Body, Request
from fastapi.security import OAuth2PasswordRequestForm
import logging

from app.identity_access.deps import get_current_user
from app.identity_access.infrastructure.db.user import User
from app.identity_access.deps import get_identity_access_application_service
from app.identity_access.application import IdentityAccessApplicationService
from app.identity_access.schemas.token import Token, RefreshTokenRequest
from app.identity_access.schemas.user import UserCreate, UserUpdate, UserResponse, SwitchRoleRequest, RoleResponse
from app.core.api import ApiResponse, BusinessException, ErrorCode, SystemException

router = APIRouter()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def _handle_unexpected_error(message: str, exc: Exception) -> BusinessException:
    """
    将未预期异常转换为统一的业务异常，遵循错误处理规范
    """
    logger.error(message, exc_info=True)
    return SystemException(
        message=message,
        code=ErrorCode.SYSTEM_ERROR,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@router.post("/login", response_model=ApiResponse[Token])
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    identity_access_service: IdentityAccessApplicationService = Depends(
        get_identity_access_application_service
    ),
) -> ApiResponse[Token]:
    """
    用户登录

    使用邮箱和密码登录系统，返回JWT令牌
    """
    logger.debug("尝试用户登录: username=%s", form_data.username)
    try:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")

        token = await identity_access_service.login(
            username_or_email=form_data.username,
            password=form_data.password,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        logger.debug("用户登录成功: username=%s", form_data.username)
        return ApiResponse.success(data=token, message="登录成功")
    except ValueError as exc:
        logger.warning("登录失败: %s - username=%s", str(exc), form_data.username)
        raise BusinessException(
            message=str(exc),
            code=ErrorCode.PERMISSION_DENIED,
            status_code=status.HTTP_401_UNAUTHORIZED,
        ) from exc
    except Exception as exc:
        raise _handle_unexpected_error("登录失败，请稍后重试", exc)


@router.post(
    "/register",
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
)
async def register(
    *,
    user_in: UserCreate = Body(...),
    identity_access_service: IdentityAccessApplicationService = Depends(
        get_identity_access_application_service
    ),
) -> ApiResponse[UserResponse]:
    """
    用户注册

    创建新用户，并返回用户信息
    """
    try:
        if not user_in.roles:
            user_in.roles = ["customer"]

        user_response = await identity_access_service.create_user(user_in)

        # TODO: 异步处理注册自动化流程

        return ApiResponse.success(data=user_response, message="注册成功")
    except ValueError as exc:
        raise BusinessException(
            message=str(exc),
            code=ErrorCode.VALIDATION_ERROR,
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc
    except Exception as exc:
        raise _handle_unexpected_error("注册失败，请稍后重试", exc)


@router.post("/refresh-token", response_model=ApiResponse[Token])
async def refresh_token(
    refresh_token_request: RefreshTokenRequest,
    identity_access_service: IdentityAccessApplicationService = Depends(
        get_identity_access_application_service
    ),
) -> ApiResponse[Token]:
    """
    刷新访问令牌
    """
    try:
        token = await identity_access_service.refresh_token(refresh_token_request)
        return ApiResponse.success(data=token, message="刷新令牌成功")
    except ValueError as exc:
        logger.warning("刷新令牌失败: %s", str(exc))
        raise BusinessException(
            message=str(exc),
            code=ErrorCode.PERMISSION_DENIED,
            status_code=status.HTTP_401_UNAUTHORIZED,
        ) from exc
    except Exception as exc:
        raise _handle_unexpected_error("刷新令牌失败，请稍后重试", exc)


@router.get("/me", response_model=ApiResponse[UserResponse])
async def read_users_me(
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(
        get_identity_access_application_service
    ),
) -> ApiResponse[UserResponse]:
    """
    获取当前用户信息
    """
    try:
        user_response = await identity_access_service.get_user_by_id(
            str(current_user.id)
        )
        if not user_response:
            raise BusinessException(
                message="用户不存在",
                code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return ApiResponse.success(data=user_response, message="获取用户信息成功")
    except BusinessException:
        raise
    except Exception as exc:
        raise _handle_unexpected_error("获取用户信息失败", exc)


@router.put("/me", response_model=ApiResponse[UserResponse])
async def update_user_me(
    *,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(
        get_identity_access_application_service
    ),
) -> ApiResponse[UserResponse]:
    """
    更新当前用户信息
    """
    try:
        user_response = await identity_access_service.update_user(
            user_id=str(current_user.id),
            user_data=user_in,
        )
        return ApiResponse.success(data=user_response, message="更新用户信息成功")
    except ValueError as exc:
        raise BusinessException(
            message=str(exc),
            code=ErrorCode.VALIDATION_ERROR,
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc
    except Exception as exc:
        raise _handle_unexpected_error("更新用户信息失败", exc)


@router.get("/roles", response_model=ApiResponse[List[str]])
async def get_roles(
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(
        get_identity_access_application_service
    ),
) -> ApiResponse[List[str]]:
    """
    获取用户角色
    """
    try:
        user_roles = await identity_access_service.get_user_roles(str(current_user.id))
        return ApiResponse.success(data=user_roles, message="获取角色成功")
    except Exception as exc:
        raise _handle_unexpected_error("获取用户角色失败", exc)


@router.get("/roles/details", response_model=ApiResponse[List[RoleResponse]])
async def get_roles_details(
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(
        get_identity_access_application_service
    ),
) -> ApiResponse[List[RoleResponse]]:
    """
    获取用户角色详情（包含显示名称等）
    """
    try:
        role_details = await identity_access_service.get_user_role_details(str(current_user.id))
        return ApiResponse.success(data=role_details, message="获取角色详情成功")
    except Exception as exc:
        raise _handle_unexpected_error("获取用户角色详情失败", exc)


@router.post("/switch-role", response_model=ApiResponse[Token])
async def switch_role(
    *,
    role_request: SwitchRoleRequest = Body(...),
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(
        get_identity_access_application_service
    ),
) -> ApiResponse[Token]:
    """
    切换用户角色
    """
    try:
        token = await identity_access_service.switch_role(
            user_id=str(current_user.id),
            target_role=role_request.role,
        )
        return ApiResponse.success(data=token, message="切换角色成功")
    except ValueError as exc:
        raise BusinessException(
            message=str(exc),
            code=ErrorCode.PERMISSION_DENIED,
            status_code=status.HTTP_403_FORBIDDEN,
        ) from exc
    except Exception as exc:
        raise _handle_unexpected_error("切换角色失败", exc)