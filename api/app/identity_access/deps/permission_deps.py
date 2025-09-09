"""
权限检查依赖函数

提供基于数据库配置的权限检查功能，替代硬编码角色检查。
"""

import logging
from typing import List, Optional, Callable, Any
from fastapi import HTTPException, status, Depends

from ..domain.entities.user import User
from ..application.identity_access_application_service import IdentityAccessApplicationService

logger = logging.getLogger(__name__)


def get_identity_access_service() -> IdentityAccessApplicationService:
    """获取身份访问应用服务依赖"""
    # 这里需要从依赖注入容器获取服务实例
    # 暂时返回None，实际使用时需要正确注入
    from .auth_deps import get_identity_access_application_service
    return get_identity_access_application_service()


async def check_user_permission(
    user: User,
    permission: str,
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_service)
) -> bool:
    """检查用户是否有指定权限"""
    if not identity_service:
        logger.warning("身份访问服务未配置，使用传统权限检查")
        # 回退到传统检查
        return _check_legacy_permission(user, permission)
    
    try:
        return await identity_service.check_user_permission_use_case(user.id, permission)
    except Exception as e:
        logger.error(f"权限检查失败: {str(e)}")
        return False


async def check_user_role(
    user: User,
    role_name: str,
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_service)
) -> bool:
    """检查用户是否有指定角色"""
    if not identity_service:
        logger.warning("身份访问服务未配置，使用传统角色检查")
        # 回退到传统检查
        return _check_legacy_role(user, role_name)
    
    try:
        return await identity_service.check_user_role_use_case(user.id, role_name)
    except Exception as e:
        logger.error(f"角色检查失败: {str(e)}")
        return False


async def check_user_any_role(
    user: User,
    role_names: List[str],
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_service)
) -> bool:
    """检查用户是否有任意一个指定角色"""
    if not identity_service:
        logger.warning("身份访问服务未配置，使用传统角色检查")
        # 回退到传统检查
        return _check_legacy_any_role(user, role_names)
    
    try:
        for role_name in role_names:
            if await identity_service.check_user_role_use_case(user.id, role_name):
                return True
        return False
    except Exception as e:
        logger.error(f"角色检查失败: {str(e)}")
        return False


async def check_user_any_permission(
    user: User,
    permissions: List[str],
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_service)
) -> bool:
    """检查用户是否有任意一个指定权限"""
    if not identity_service:
        logger.warning("身份访问服务未配置，使用传统权限检查")
        # 回退到传统检查
        return _check_legacy_any_permission(user, permissions)
    
    try:
        for permission in permissions:
            if await identity_service.check_user_permission_use_case(user.id, permission):
                return True
        return False
    except Exception as e:
        logger.error(f"权限检查失败: {str(e)}")
        return False


async def is_user_admin(
    user: User,
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_service)
) -> bool:
    """检查用户是否为管理员"""
    if not identity_service:
        logger.warning("身份访问服务未配置，使用传统管理员检查")
        # 回退到传统检查
        return _check_legacy_admin(user)
    
    try:
        return await identity_service.is_user_admin_use_case(user.id)
    except Exception as e:
        logger.error(f"管理员权限检查失败: {str(e)}")
        return False


# ==================== 权限装饰器 ====================

def require_permission(permission: str):
    """要求指定权限的装饰器"""
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            # 从参数中获取用户对象
            user = None
            for arg in args:
                if isinstance(arg, User):
                    user = arg
                    break
            
            if not user:
                for key, value in kwargs.items():
                    if isinstance(value, User):
                        user = value
                        break
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户未认证"
                )
            
            # 检查权限
            has_permission = await check_user_permission(user, permission)
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"缺少权限: {permission}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(role_name: str):
    """要求指定角色的装饰器"""
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            # 从参数中获取用户对象
            user = None
            for arg in args:
                if isinstance(arg, User):
                    user = arg
                    break
            
            if not user:
                for key, value in kwargs.items():
                    if isinstance(value, User):
                        user = value
                        break
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户未认证"
                )
            
            # 检查角色
            has_role = await check_user_role(user, role_name)
            if not has_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"缺少角色: {role_name}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_any_role(role_names: List[str]):
    """要求任意一个指定角色的装饰器"""
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            # 从参数中获取用户对象
            user = None
            for arg in args:
                if isinstance(arg, User):
                    user = arg
                    break
            
            if not user:
                for key, value in kwargs.items():
                    if isinstance(value, User):
                        user = value
                        break
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户未认证"
                )
            
            # 检查角色
            has_any_role = await check_user_any_role(user, role_names)
            if not has_any_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"缺少角色: {', '.join(role_names)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_admin():
    """要求管理员权限的装饰器"""
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            # 从参数中获取用户对象
            user = None
            for arg in args:
                if isinstance(arg, User):
                    user = arg
                    break
            
            if not user:
                for key, value in kwargs.items():
                    if isinstance(value, User):
                        user = value
                        break
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户未认证"
                )
            
            # 检查管理员权限
            is_admin = await is_user_admin(user)
            if not is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="需要管理员权限"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# ==================== 传统权限检查（向后兼容） ====================

def _check_legacy_permission(user: User, permission: str) -> bool:
    """传统权限检查（向后兼容）"""
    # 这里实现传统的权限检查逻辑
    # 可以根据需要调用现有的权限检查方法
    return True  # 临时实现


def _check_legacy_role(user: User, role_name: str) -> bool:
    """传统角色检查（向后兼容）"""
    # 检查用户角色集合
    return role_name in user.roles


def _check_legacy_any_role(user: User, role_names: List[str]) -> bool:
    """传统任意角色检查（向后兼容）"""
    return any(role_name in user.roles for role_name in role_names)


def _check_legacy_any_permission(user: User, permissions: List[str]) -> bool:
    """传统任意权限检查（向后兼容）"""
    # 这里实现传统的权限检查逻辑
    return True  # 临时实现


def _check_legacy_admin(user: User) -> bool:
    """传统管理员检查（向后兼容）"""
    admin_roles = ["administrator", "operator"]
    return any(role in admin_roles for role in user.roles)
