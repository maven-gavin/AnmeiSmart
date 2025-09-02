"""
认证相关依赖模块 - 用户认证、权限控制等

专注于权限检查工具函数，从security_deps.py导入核心认证依赖。
遵循DDD分层架构，避免重复定义。
"""

from fastapi import Depends, HTTPException, status
from typing import List
import logging

from app.identity_access.deps.security_deps import get_current_user, oauth2_scheme
from app.identity_access.infrastructure.db.user import User

logger = logging.getLogger(__name__)


# 获取当前管理员用户 - 从security_deps.py导入，避免重复
from app.identity_access.deps.security_deps import get_current_admin

# 别名，用于更明确的语义
require_admin_role = get_current_admin


def get_user_roles(user: User) -> List[str]:
    """获取用户角色列表"""
    roles = [role.name for role in user.roles]
    logger.debug(f"用户 {user.id} 的角色: {roles}")
    return roles


def check_user_has_role(user: User, role_name: str) -> bool:
    """检查用户是否有指定角色"""
    has_role = any(role.name == role_name for role in user.roles)
    logger.debug(f"检查用户 {user.id} 是否有角色 {role_name}: {has_role}")
    return has_role


def require_role(role_name: str):
    """
    要求用户具有指定角色的装饰器工厂函数
    
    Args:
        role_name: 所需的角色名称
        
    Returns:
        函数: 检查用户角色的依赖函数
    """
    async def check_role(
        current_user: User = Depends(get_current_user)
    ) -> User:
        """检查用户是否有指定角色"""
        if not check_user_has_role(current_user, role_name):
            logger.warning(f"权限不足: 用户 {current_user.id} 缺少角色 {role_name}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要角色权限: {role_name}",
            )
        return current_user
    
    return check_role


def require_any_role(role_names: List[str]):
    """
    要求用户具有指定角色列表中任一角色的装饰器工厂函数
    
    Args:
        role_names: 所需的角色名称列表
        
    Returns:
        函数: 检查用户角色的依赖函数
    """
    async def check_any_role(
        current_user: User = Depends(get_current_user)
    ) -> User:
        """检查用户是否有指定角色列表中的任一角色"""
        user_roles = get_user_roles(current_user)
        if not any(role in user_roles for role in role_names):
            logger.warning(f"权限不足: 用户 {current_user.id} 缺少所需角色 {role_names}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要以下角色之一: {', '.join(role_names)}",
            )
        return current_user
    
    return check_any_role


# 导出所有依赖函数
__all__ = [
    "oauth2_scheme",
    "get_current_user", 
    "get_current_admin", 
    "require_admin_role", 
    "get_user_roles", 
    "check_user_has_role",
    "require_role",
    "require_any_role"
]
