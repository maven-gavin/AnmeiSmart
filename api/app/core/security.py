from datetime import datetime, timedelta
from typing import Any, Union, Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import get_db
from app.crud import crud_user
from app.db.models.user import User

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)

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
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # 从令牌中提取活跃角色
        active_role: str = payload.get("role")
    except JWTError:
        raise credentials_exception
    
    user = await crud_user.get(db, id=int(user_id))
    if user is None:
        raise credentials_exception
    
    # 如果令牌包含活跃角色，将其作为属性添加到用户对象
    if active_role:
        # 检查用户是否拥有此角色
        user_roles = [role.name for role in user.roles]
        if active_role not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户没有请求的角色权限",
            )
        # 使用下划线前缀避免与数据库字段冲突
        setattr(user, "_active_role", active_role)
    
    return user

def check_role_permission(required_roles: list[str] = None):
    """
    检查用户是否有所需角色的装饰器工厂函数
    
    Args:
        required_roles: 所需的角色列表
        
    Returns:
        函数: 检查用户角色的依赖函数
    """
    async def check_permission(current_user: User = Depends(get_current_user)):
        # 如果未指定所需角色，允许任何已认证用户访问
        if not required_roles:
            return current_user
            
        # 获取当前用户的活跃角色
        active_role = getattr(current_user, "_active_role", None)
        
        # 如果未设置活跃角色，使用用户的任何角色
        if not active_role:
            user_roles = [role.name for role in current_user.roles]
            # 检查用户是否拥有任何所需角色
            if any(role in required_roles for role in user_roles):
                return current_user
        # 否则只检查活跃角色
        elif active_role in required_roles:
            return current_user
            
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户权限不足",
        )
    
    return check_permission 