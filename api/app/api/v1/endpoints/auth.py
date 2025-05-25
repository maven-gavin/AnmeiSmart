from datetime import timedelta
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt, JWTError
import logging

from app.core.config import get_settings
from app.core.security import create_access_token, get_current_user
from app.db.base import get_db
from app.db.models.user import User
from app.crud import crud_user
from app.schemas.token import Token
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
        user = await crud_user.authenticate(
            db, username_or_email=form_data.username, password=form_data.password
        )
        if not user:
            logger.warning(f"登录失败: 用户名或密码错误 - username={form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        elif not user.is_active:
            logger.warning(f"登录失败: 用户未激活 - username={form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户未激活"
            )
        
        # 获取用户的第一个角色作为默认活跃角色
        active_role = user.roles[0].name if user.roles else None
        logger.debug(f"用户登录成功: username={form_data.username}, user_id={user.id}, active_role={active_role}")
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.id, expires_delta=access_token_expires, active_role=active_role
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    except Exception as e:
        logger.error(f"登录过程中发生异常: {str(e)}", exc_info=True)
        raise

@router.post("/register", response_model=UserResponse)
async def register(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    用户注册
    
    创建新用户，并返回用户信息
    """
    user = await crud_user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="此邮箱已注册",
        )
    
    # 确保公开注册的用户至少有顾客角色
    if not user_in.roles or len(user_in.roles) == 0:
        user_in.roles = ["customer"]
    
    user = await crud_user.create(db, obj_in=user_in)
    
    # 获取用户的第一个角色作为默认活跃角色
    active_role = user.roles[0].name if user.roles else None
    
    return UserResponse.from_orm(user, active_role=active_role)

@router.post("/refresh-token", response_model=Token)
async def refresh_token(
    db: Session = Depends(get_db),
    token: str = Body(..., embed=True)
) -> Any:
    """
    刷新访问令牌
    
    使用过期的令牌获取新的访问令牌。即使令牌已过期，仍然尝试解析用户ID和角色信息。
    """
    try:
        # 尝试解码令牌，即使过期也允许
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False}  # 不验证过期时间
        )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌",
            )
        
        # 获取用户信息 - 直接使用用户ID，不转换为整数
        user = await crud_user.get(db, id=user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在或未激活",
            )
        
        # 从原令牌中获取活跃角色
        active_role = payload.get("role")
        if active_role:
            # 验证用户是否仍然具有该角色
            user_roles = [role.name for role in user.roles]
            if active_role not in user_roles:
                # 如果不再有该角色，使用第一个可用角色
                active_role = user_roles[0] if user_roles else None
        else:
            # 如果原令牌没有活跃角色，使用第一个可用角色
            active_role = user.roles[0].name if user.roles else None
        
        # 创建新令牌
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.id, 
            expires_delta=access_token_expires, 
            active_role=active_role
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"无效的JWT令牌格式: {str(e)}",
        )    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"无法刷新令牌: {str(e)}",
        )

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    获取当前用户信息
    
    返回当前已认证用户的详细信息
    """
    # 从当前令牌中获取活跃角色
    active_role = current_user._active_role if hasattr(current_user, "_active_role") else None
    
    return UserResponse.from_orm(current_user, active_role=active_role)

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
    user = await crud_user.update(db, db_obj=current_user, obj_in=user_in)
    
    # 从当前令牌中获取活跃角色
    active_role = current_user._active_role if hasattr(current_user, "_active_role") else None
    
    return UserResponse.from_orm(user, active_role=active_role)

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
    user_roles = await crud_user.get_user_roles(db, user_id=current_user.id)
    return user_roles

@router.post("/switch-role", response_model=Token)
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
    # 检查用户是否拥有请求的角色
    user_roles = [role.name for role in current_user.roles]
    if role_request.role not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"用户没有 '{role_request.role}' 角色权限",
        )
    
    # 生成包含新活跃角色的令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=current_user.id, 
        expires_delta=access_token_expires,
        active_role=role_request.role
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    } 