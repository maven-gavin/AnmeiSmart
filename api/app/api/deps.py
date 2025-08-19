from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from typing import Generator, Optional, List
import logging

from app.db.base import get_db
from app.core.config import get_settings
from app.core.security import verify_token, get_current_user
from app.db.models.user import User

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# 设置更详细的日志级别
logger.setLevel(logging.DEBUG)

settings = get_settings()

# OAuth2 密码流验证
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

# 获取当前管理员用户
def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if not any(role.name == "admin" for role in current_user.roles):
        logger.warning(f"权限不足: 用户 {current_user.id} 不是管理员")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户权限不足，需要管理员权限",
        )
    return current_user

# 别名，用于更明确的语义
require_admin_role = get_current_admin

# 获取当前用户的角色列表
def get_user_roles(user: User) -> List[str]:
    roles = [role.name for role in user.roles]
    logger.debug(f"用户 {user.id} 的角色: {roles}")
    return roles

# 检查用户是否有指定角色
def check_user_has_role(user: User, role_name: str) -> bool:
    has_role = any(role.name == role_name for role in user.roles)
    logger.debug(f"检查用户 {user.id} 是否有角色 {role_name}: {has_role}")
    return has_role 