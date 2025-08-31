from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import logging

from app.core.config import get_settings
from app.db.base import get_db
from app.core.password_utils import verify_password
# from app.services import user_service  # 已重构为DDD架构，不再需要
from app.db.models import User

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# 设置更详细的日志级别
logger.setLevel(logging.DEBUG)

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def verify_token(token: str) -> Optional[str]:
    """
    验证JWT令牌并提取用户ID
    
    Args:
        token: JWT令牌
    
    Returns:
        str: 用户ID，如果令牌无效则返回None
    """
    # 记录令牌前几个字符，避免完整记录敏感信息
    token_prefix = token[:10] if token and len(token) > 10 else "无token"
    logger.debug(f"开始验证令牌: {token_prefix}...")
    
    try:
        logger.debug(f"尝试解码令牌...")
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        logger.debug(f"令牌解码成功")
        
        user_id = payload.get("sub")
        if user_id is None:
            logger.warning(f"令牌有效但未包含用户ID(sub)信息")
            return None
        
        # 检查令牌是否过期
        exp = payload.get("exp")
        if exp:
            current_time = datetime.utcnow().timestamp()
            if current_time > exp:
                logger.warning(f"令牌已过期: 过期时间={datetime.fromtimestamp(exp).isoformat()}")
                return None
            
        logger.debug(f"令牌验证成功: user_id={user_id}")
        return user_id
    except JWTError as e:
        logger.warning(f"令牌验证失败: JWT错误 - {str(e)}")
        return None
    except Exception as e:
        logger.error(f"令牌验证过程中发生未知错误: {str(e)}")
        return None

def create_access_token(
    subject: Union[str, Any], 
    expires_delta: Optional[timedelta] = None,
    active_role: Optional[str] = None
) -> str:
    """
    创建访问令牌
    
    Args:
        subject: 令牌主体 (通常是用户ID)
        expires_delta: 过期时间增量
        active_role: 用户当前活跃角色
        
    Returns:
        str: JWT令牌
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    
    # 如果提供了活跃角色，将其添加到令牌中
    if active_role:
        to_encode["role"] = active_role
    
    logger.debug(f"创建访问令牌: user_id={subject}, 过期时间={expire.isoformat()}, 活跃角色={active_role}")
    
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def create_refresh_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
    active_role: Optional[str] = None
) -> str:
    """
    创建刷新令牌
    
    Args:
        subject: 令牌主体 (通常是用户ID)
        expires_delta: 过期时间增量
        active_role: 用户当前活跃角色
        
    Returns:
        str: JWT刷新令牌
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    
    # 如果提供了活跃角色，将其添加到令牌中
    if active_role:
        to_encode["role"] = active_role
    
    logger.debug(f"创建刷新令牌: user_id={subject}, 过期时间={expire.isoformat()}, 活跃角色={active_role}")
    
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt

async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    获取当前用户
    
    从JWT令牌中解析出用户ID和活跃角色，并获取用户对象
    
    Args:
        db: 数据库会话
        token: JWT令牌
    
    Returns:
        User: 用户对象
    
    Raises:
        HTTPException: 如果令牌无效或用户不存在
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 记录令牌前几个字符，避免完整记录敏感信息
    token_prefix = token[:10] if token and len(token) > 10 else "无token"
    logger.debug(f"开始验证当前用户令牌: {token_prefix}...")
    
    try:
        logger.debug(f"尝试解码令牌...")
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        logger.debug(f"令牌解码成功")
        
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.warning(f"令牌有效但未包含用户ID(sub)信息")
            raise credentials_exception
        
        # 检查令牌是否过期
        exp = payload.get("exp")
        if exp:
            current_time = datetime.utcnow().timestamp()
            if current_time > exp:
                logger.warning(f"令牌已过期: 过期时间={datetime.fromtimestamp(exp).isoformat()}")
                raise credentials_exception
        
        # 从令牌中提取活跃角色
        active_role: str = payload.get("role")
        logger.debug(f"令牌解析结果: user_id={user_id}, 活跃角色={active_role}")
    except JWTError as e:
        logger.warning(f"JWT解码错误: {str(e)}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"令牌验证过程中发生未知错误: {str(e)}")
        raise credentials_exception
    
    logger.debug(f"尝试从数据库获取用户: user_id={user_id}")
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        logger.warning(f"无法在数据库中找到用户: user_id={user_id}")
        raise credentials_exception
    
    logger.debug(f"成功获取用户: id={user.id}, email={user.email}, 角色数={len(user.roles) if user.roles else 0}")
    
    # 如果令牌包含活跃角色，将其作为属性添加到用户对象
    if active_role:
        # 检查用户是否拥有此角色
        user_roles = [role.name if hasattr(role, 'name') else role for role in user.roles]
        logger.debug(f"用户角色: {user_roles}, 令牌指定角色: {active_role}")
        
        if active_role not in user_roles:
            logger.warning(f"用户 {user.id} 没有令牌指定的角色权限: {active_role}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户没有请求的角色权限",
            )
        # 使用下划线前缀避免与数据库字段冲突
        setattr(user, "_active_role", active_role)
        logger.debug(f"为用户 {user.id} 设置活跃角色: {active_role}")
    
    return user

def check_role_permission(required_roles: list[str] = None):
    """
    检查用户是否有所需角色的装饰器工厂函数
    
    Args:
        required_roles: 所需的角色列表
        
    Returns:
        函数: 检查用户角色的依赖函数
    """
    async def check_permission(current_user: Any = Depends(get_current_user)):
        # 如果未指定所需角色，允许任何已认证用户访问
        if not required_roles:
            logger.debug(f"未指定所需角色，允许用户 {current_user.id} 访问")
            return current_user
            
        # 获取当前用户的活跃角色
        active_role = getattr(current_user, "_active_role", None)
        logger.debug(f"检查用户 {current_user.id} 的权限, 活跃角色: {active_role}, 所需角色: {required_roles}")
        
        # 如果未设置活跃角色，使用用户的任何角色
        if not active_role:
            user_roles = [role.name for role in current_user.roles]
            logger.debug(f"用户 {current_user.id} 的所有角色: {user_roles}")
            
            # 检查用户是否拥有任何所需角色
            if any(role in required_roles for role in user_roles):
                matching_roles = [role for role in user_roles if role in required_roles]
                logger.debug(f"用户 {current_user.id} 拥有所需角色: {matching_roles}")
                return current_user
            logger.warning(f"用户 {current_user.id} 没有所需角色: {required_roles}")
        # 否则只检查活跃角色
        elif active_role in required_roles:
            logger.debug(f"用户 {current_user.id} 的活跃角色 {active_role} 符合要求")
            return current_user
        else:
            logger.warning(f"用户 {current_user.id} 的活跃角色 {active_role} 不符合要求: {required_roles}")
            
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户权限不足",
        )
    
    return check_permission 


async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    获取当前管理员用户
    
    检查当前用户是否具有管理员权限
    
    Args:
        current_user: 当前认证用户
    
    Returns:
        User: 管理员用户对象
    
    Raises:
        HTTPException: 如果用户不是管理员
    """
    # 获取用户角色列表
    user_roles = [role.name if hasattr(role, 'name') else role for role in current_user.roles]
    
    # 检查是否有管理员角色
    if "admin" not in user_roles:
        logger.warning(f"用户 {current_user.id} 尝试访问管理员功能但不是管理员，当前角色: {user_roles}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    
    logger.debug(f"管理员用户验证通过: {current_user.id}")
    return current_user