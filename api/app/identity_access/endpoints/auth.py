from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Body, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
import logging

from app.core.config import get_settings
from app.identity_access.deps import get_current_user
from app.identity_access.infrastructure.db.user import User
from app.identity_access.deps.identity_access import get_identity_access_application_service
from app.identity_access.application import IdentityAccessApplicationService
from app.identity_access.schemas.token import Token, RefreshTokenRequest
from app.identity_access.schemas.user import UserCreate, UserUpdate, UserResponse, SwitchRoleRequest

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> Any:
    """
    用户登录
    
    使用邮箱和密码登录系统，返回JWT令牌
    """
    logger.debug(f"尝试用户登录: username={form_data.username}")
    try:
        # 获取客户端信息
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")
        
        # 调用应用服务进行登录
        token = await identity_access_service.login_use_case(
            username_or_email=form_data.username,
            password=form_data.password,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.debug(f"用户登录成功: username={form_data.username}")
        return token
        
    except ValueError as e:
        logger.warning(f"登录失败: {str(e)} - username={form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"登录过程中发生异常: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败，请稍后重试"
        )

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    *,
    user_in: UserCreate = Body(...),
    background_tasks: BackgroundTasks,
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> Any:
    """
    用户注册
    
    创建新用户，并返回用户信息
    """
    try:
        # 确保公开注册的用户至少有客户角色
        if not user_in.roles or len(user_in.roles) == 0:
            user_in.roles = ["customer"]
        
        # 调用应用服务创建用户
        user_response = await identity_access_service.create_user_use_case(user_in)

        # 用户注册自动化流程：
        # 1、创建默认的会话，启用AI功能
        # 2、通过AI Gateway触发Dify Agent，调用MCP查询用户信息，生成定制的欢迎语
        # 3、顾问端收到新客户通知，可以认领客户提供专业咨询服务
        user_info = {
            "username": user_response.username,
            "email": user_response.email,
            "roles": user_response.roles,
            "phone": user_response.phone,
            "avatar": user_response.avatar
        }
        
        # TODO: 异步处理注册自动化流程
        
        return user_response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"用户注册异常: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败，请稍后重试"
        )

@router.post("/refresh-token", response_model=Token)
async def refresh_token(
    refresh_token_request: RefreshTokenRequest,
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> Any:
    """
    刷新访问令牌
    
    使用刷新令牌获取新的访问令牌。即使令牌已过期，仍然尝试解析用户ID和角色信息。
    """
    try:
        # 调用应用服务刷新令牌
        token = await identity_access_service.refresh_token_use_case(refresh_token_request)
        return token
        
    except ValueError as e:
        logger.warning(f"刷新令牌失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"刷新令牌异常: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="刷新令牌失败，请稍后重试"
        )

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> Any:
    """
    获取当前用户信息
    
    返回当前已认证用户的详细信息
    """
    try:
        user_response = await identity_access_service.get_user_by_id_use_case(str(current_user.id))
        if not user_response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        return user_response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户信息失败"
        )

@router.put("/me", response_model=UserResponse)
async def update_user_me(
    *,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> Any:
    """
    更新当前用户信息
    
    允许用户更新自己的信息
    """
    try:
        user_response = await identity_access_service.update_user_use_case(
            user_id=str(current_user.id),
            user_data=user_in
        )
        return user_response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"更新用户信息失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户信息失败"
        )

@router.get("/roles", response_model=List[str])
async def get_roles(
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> Any:
    """
    获取用户角色
    
    返回当前用户的所有角色
    """
    try:
        user_roles = await identity_access_service.get_user_roles_use_case(str(current_user.id))
        return user_roles
    except Exception as e:
        logger.error(f"获取用户角色失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户角色失败"
        )

@router.post("/switch-role", response_model=Token)
async def switch_role(
    *,
    role_request: SwitchRoleRequest,
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> Any:
    """
    切换用户角色
    
    更改用户当前活跃角色，并返回新的访问令牌和刷新令牌
    """
    try:
        token = await identity_access_service.switch_role_use_case(
            user_id=str(current_user.id),
            target_role=role_request.role
        )
        return token
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"切换角色失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="切换角色失败"
        ) 