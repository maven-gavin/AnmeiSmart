"""
权限检查依赖函数

提供基于数据库配置的权限检查功能，替代硬编码角色检查。
符合API标准：使用BusinessException和ErrorCode。
"""

import logging
from functools import wraps
from typing import List, Optional, Callable, Any
from fastapi import status, Depends
from sqlalchemy.orm import Session

from ..domain.entities.user import UserEntity
from ..infrastructure.db.user import User
from ..application.identity_access_application_service import IdentityAccessApplicationService
from ..domain.role_permission_domain_service import RolePermissionDomainService
from app.core.api import BusinessException, ErrorCode

logger = logging.getLogger(__name__)


def get_identity_access_service() -> IdentityAccessApplicationService:
    """获取身份访问应用服务依赖"""
    from .auth_deps import get_identity_access_application_service
    return get_identity_access_application_service()


async def check_user_permission(
    user: UserEntity,
    permission: str,
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_service)
) -> bool:
    """检查用户是否有指定权限"""
    try:
        return await identity_service.check_user_permission_use_case(user.id, permission)
    except Exception as e:
        logger.error(f"权限检查失败: {str(e)}")
        # 回退到传统检查
        return _check_legacy_permission(user, permission)


async def check_user_role(
    user: UserEntity,
    role_name: str,
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_service)
) -> bool:
    """检查用户是否有指定角色"""
    try:
        return await identity_service.check_user_role_use_case(user.id, role_name)
    except Exception as e:
        logger.error(f"角色检查失败: {str(e)}")
        # 回退到传统检查
        return _check_legacy_role(user, role_name)


async def check_user_any_role(
    user: UserEntity,
    role_names: List[str],
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_service)
) -> bool:
    """检查用户是否有任意一个指定角色"""
    try:
        for role_name in role_names:
            if await identity_service.check_user_role_use_case(user.id, role_name):
                return True
        return False
    except Exception as e:
        logger.error(f"角色检查失败: {str(e)}")
        # 回退到传统检查
        return _check_legacy_any_role(user, role_names)


async def check_user_any_permission(
    user: UserEntity,
    permissions: List[str],
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_service)
) -> bool:
    """检查用户是否有任意一个指定权限"""
    try:
        for permission in permissions:
            if await identity_service.check_user_permission_use_case(user.id, permission):
                return True
        return False
    except Exception as e:
        logger.error(f"权限检查失败: {str(e)}")
        # 回退到传统检查
        return _check_legacy_any_permission(user, permissions)


async def is_user_admin(
    user: UserEntity,
    identity_service: IdentityAccessApplicationService = Depends(get_identity_access_service)
) -> bool:
    """检查用户是否为管理员"""
    try:
        return await identity_service.is_user_admin_use_case(user.id)
    except Exception as e:
        logger.error(f"管理员权限检查失败: {str(e)}")
        # 回退到传统检查
        return _check_legacy_admin(user)


# ==================== 权限装饰器 ====================



def require_role(role_name: str):
    """要求指定角色的装饰器"""
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            # 从参数中获取用户对象
            user = None
            for arg in args:
                if isinstance(arg, UserEntity):
                    user = arg
                    break
            
            if not user:
                for key, value in kwargs.items():
                    if isinstance(value, UserEntity):
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
                if isinstance(arg, UserEntity):
                    user = arg
                    break
            
            if not user:
                for key, value in kwargs.items():
                    if isinstance(value, UserEntity):
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
    """要求管理员权限的装饰器（符合API标准）"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从kwargs中获取current_user（FastAPI会自动注入）
            current_user = kwargs.get('current_user')
            if not current_user:
                # 尝试从args中获取
                for arg in args:
                    if isinstance(arg, User) or isinstance(arg, UserEntity):
                        current_user = arg
                        break
            
            if not current_user:
                raise BusinessException(
                    message="用户未认证",
                    code=ErrorCode.VALIDATION_ERROR,
                    status_code=status.HTTP_401_UNAUTHORIZED,
                )
            
            # 直接调用领域服务进行权限验证
            from .auth_deps import get_role_permission_domain_service
            from app.common.infrastructure.db.base import get_db
            from sqlalchemy.orm import Session
            
            # 获取数据库会话和领域服务
            db: Session = kwargs.get('_db') or kwargs.get('db')
            if not db:
                # 如果kwargs中没有db，尝试从args获取
                for arg in args:
                    if isinstance(arg, Session):
                        db = arg
                        break
            
            if db:
                from ..infrastructure.repositories.user_repository import UserRepository
                from ..infrastructure.repositories.role_repository import RoleRepository
                from ..infrastructure.repositories.permission_repository import PermissionRepository
                from ..converters.user_converter import UserConverter
                from ..converters.role_converter import RoleConverter
                
                user_repository = UserRepository(db, UserConverter())
                role_repository = RoleRepository(db, RoleConverter())
                permission_repository = PermissionRepository(db)
                
                role_permission_service = RolePermissionDomainService(
                    role_repository, permission_repository, user_repository
                )
                
                user_id = str(current_user.id) if hasattr(current_user, 'id') else current_user
                is_admin = await role_permission_service.is_user_admin(user_id)
            else:
                # 回退到应用服务检查
                identity_service = kwargs.get('identity_service')
                if not identity_service:
                    from .auth_deps import get_identity_access_application_service
                    identity_service = get_identity_access_application_service()
                
                user_id = str(current_user.id) if hasattr(current_user, 'id') else current_user
                is_admin = await identity_service.is_user_admin_use_case(user_id)
            
            if not is_admin:
                raise BusinessException(
                    message="没有足够的权限执行此操作",
                    code=ErrorCode.PERMISSION_DENIED,
                    status_code=status.HTTP_403_FORBIDDEN,
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_permission(permission: str):
    """权限装饰器：声明API需要指定权限（符合API标准）"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从kwargs中获取current_user（FastAPI会自动注入）
            current_user = kwargs.get('current_user')
            if not current_user:
                # 尝试从args中获取
                for arg in args:
                    if isinstance(arg, User) or isinstance(arg, UserEntity):
                        current_user = arg
                        break
            
            if not current_user:
                raise BusinessException(
                    message="用户未认证",
                    code=ErrorCode.VALIDATION_ERROR,
                    status_code=status.HTTP_401_UNAUTHORIZED,
                )
            
            # 获取数据库会话和领域服务
            db: Session = kwargs.get('_db') or kwargs.get('db')
            if not db:
                for arg in args:
                    if isinstance(arg, Session):
                        db = arg
                        break
            
            if db:
                from ..infrastructure.repositories.user_repository import UserRepository
                from ..infrastructure.repositories.role_repository import RoleRepository
                from ..infrastructure.repositories.permission_repository import PermissionRepository
                from ..converters.user_converter import UserConverter
                from ..converters.role_converter import RoleConverter
                
                user_repository = UserRepository(db, UserConverter())
                role_repository = RoleRepository(db, RoleConverter())
                permission_repository = PermissionRepository(db)
                
                role_permission_service = RolePermissionDomainService(
                    role_repository, permission_repository, user_repository
                )
                
                user_id = str(current_user.id) if hasattr(current_user, 'id') else current_user
                has_permission = await role_permission_service.check_user_permission(user_id, permission)
            else:
                # 回退到应用服务检查
                identity_service = kwargs.get('identity_service')
                if not identity_service:
                    from .auth_deps import get_identity_access_application_service
                    identity_service = get_identity_access_application_service()
                
                user_id = str(current_user.id) if hasattr(current_user, 'id') else current_user
                has_permission = await identity_service.check_user_permission_use_case(user_id, permission)
            
            if not has_permission:
                raise BusinessException(
                    message=f"缺少权限: {permission}",
                    code=ErrorCode.PERMISSION_DENIED,
                    status_code=status.HTTP_403_FORBIDDEN,
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
