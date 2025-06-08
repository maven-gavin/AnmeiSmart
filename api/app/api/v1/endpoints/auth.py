from datetime import timedelta
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt, JWTError
import logging

from app.core.config import get_settings
from app.core.security import create_access_token, get_current_user, create_refresh_token
from app.db.base import get_db
from app.db.models.user import User
from app.services import user_service
from app.schemas.token import Token, AccessToken, RefreshTokenRequest
from app.schemas.user import UserCreate, UserUpdate, UserResponse, SwitchRoleRequest

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

@router.post("/login", response_model=Token)
async def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    用户登录
    
    使用邮箱和密码登录系统，返回JWT令牌
    """
    logger.debug(f"尝试用户登录: username={form_data.username}")
    try:
        userResponse = await user_service.authenticate(
            db, username_or_email=form_data.username, password=form_data.password
        )
        if not userResponse:
            logger.warning(f"登录失败: 用户名或密码错误 - username={form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        elif not userResponse.is_active:
            logger.warning(f"登录失败: 用户未激活 - username={form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户未激活"
            )
        
        # 获取用户的第一个角色作为默认活跃角色
        active_role = userResponse.roles[0] if userResponse.roles else None
        logger.debug(f"用户登录成功: username={form_data.username}, user_id={userResponse.id}, active_role={active_role}")
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=userResponse.id, expires_delta=access_token_expires, active_role=active_role
        )
        
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token = create_refresh_token(
            subject=userResponse.id, expires_delta=refresh_token_expires, active_role=active_role
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    except Exception as e:
        logger.error(f"登录过程中发生异常: {str(e)}", exc_info=True)
        raise

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate = Body(...),
) -> Any:
    """
    用户注册
    
    创建新用户，并返回用户信息
    """
    userResponse = await user_service.get_by_email(db, email=user_in.email)
    if userResponse:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="此邮箱已注册",
        )
    
    # 确保公开注册的用户至少有顾客角色
    if not user_in.roles or len(user_in.roles) == 0:
        user_in.roles = ["customer"]
    
    userResponse = await user_service.create(db, obj_in=user_in)
    
    return userResponse

@router.post("/refresh-token", response_model=Token)
async def refresh_token(
    refresh_token_request: RefreshTokenRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    刷新访问令牌
    
    使用刷新令牌获取新的访问令牌。即使令牌已过期，仍然尝试解析用户ID和角色信息。
    """
    try:
        # 尝试解码令牌，即使过期也允许
        payload = jwt.decode(
            refresh_token_request.token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False}  # 不验证过期时间
        )
        
        # 验证令牌类型
        token_type = payload.get("type")
        if token_type != "refresh":
            logger.warning(f"无效的令牌类型: {token_type}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌类型",
            )
        
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("令牌中没有用户ID")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌",
            )
        
        # 获取用户信息
        userResponse = await user_service.get(db, id=user_id)
        if not userResponse or not userResponse.is_active:
            logger.warning(f"用户不存在或未激活: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在或未激活",
            )
        
        # 从原令牌中获取活跃角色
        active_role = payload.get("role")
        if active_role:
            # 验证用户是否仍然具有该角色
            user_roles = [role for role in userResponse.roles]
            if active_role not in user_roles:
                # 如果不再有该角色，使用第一个可用角色
                active_role = user_roles[0] if user_roles else None
                logger.info(f"用户 {user_id} 不再拥有角色 {active_role}，切换到 {active_role}")
        else:
            # 如果原令牌没有活跃角色，使用第一个可用角色
            user_roles = [role for role in userResponse.roles]
            active_role = user_roles[0] if user_roles else None
        
        # 创建新的访问令牌和刷新令牌
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=userResponse.id, 
            expires_delta=access_token_expires, 
            active_role=active_role
        )
        
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        new_refresh_token = create_refresh_token(
            subject=userResponse.id,
            expires_delta=refresh_token_expires,
            active_role=active_role
        )
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    
    except JWTError as e:
        logger.warning(f"JWT解码错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"无效的JWT令牌格式: {str(e)}",
        )    
    except Exception as e:
        logger.error(f"刷新令牌失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"无法刷新令牌: {str(e)}",
        )

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    获取当前用户信息
    
    返回当前已认证用户的详细信息
    """
    userResponse = await user_service.get(db, id=current_user.id)
    return userResponse

@router.put("/me", response_model=UserResponse)
async def update_user_me(
    *,
    db: Session = Depends(get_db),
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    更新当前用户信息
    
    允许用户更新自己的信息
    """
    user_response = await user_service.update(db, user_id=current_user.id, obj_in=user_in)
    return user_response

@router.get("/roles", response_model=List[str])
async def get_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    获取用户角色
    
    返回当前用户的所有角色
    """
    # 从数据库获取用户角色
    user_roles = await user_service.get_user_roles(db, user_id=current_user.id)
    return user_roles

@router.post("/switch-role", response_model=AccessToken)
async def switch_role(
    *,
    db: Session = Depends(get_db),
    role_request: SwitchRoleRequest,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    切换用户角色
    
    更改用户当前活跃角色，并返回新的访问令牌
    """
    # 获取真实的 User 对象
    user = db.query(User).filter(User.id == current_user.id).first()
    # 检查用户是否拥有请求的角色
    user_roles = [role.name if hasattr(role, 'name') else role for role in user.roles]
    if role_request.role not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"用户没有 '{role_request.role}' 角色权限",
        )
    
    # 生成包含新活跃角色的令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, 
        expires_delta=access_token_expires,
        active_role=role_request.role
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    } 