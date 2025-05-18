from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from typing import Generator, Optional, List

from app.db.base import get_db
from app.core.config import get_settings
from app.core.security import verify_token
from app.db.models.user import User

settings = get_settings()

# OAuth2 密码流验证
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

# 获取当前用户
def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="认证令牌无效",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 验证令牌
        user_id = verify_token(token)
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # 获取用户信息
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

# 获取当前管理员用户
def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if not any(role.name == "admin" for role in current_user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户权限不足，需要管理员权限",
        )
    return current_user

# 获取当前用户的角色列表
def get_user_roles(user: User) -> List[str]:
    return [role.name for role in user.roles]

# 检查用户是否有指定角色
def check_user_has_role(user: User, role_name: str) -> bool:
    return any(role.name == role_name for role in user.roles) 