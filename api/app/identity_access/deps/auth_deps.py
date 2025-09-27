"""
认证授权相关依赖注入配置

整合认证、授权、权限检查等所有安全相关功能。
"""

from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import logging

from app.core.config import get_settings
from app.identity_access.infrastructure.db.user import User
from app.identity_access.infrastructure.jwt_service import JWTService
from app.identity_access.domain.security_domain_service import SecurityDomainService
from app.identity_access.application.security_application_service import SecurityApplicationService
from app.identity_access.domain.tenant_domain_service import TenantDomainService
from app.identity_access.domain.role_permission_domain_service import RolePermissionDomainService
from app.identity_access.application.tenant_application_service import TenantApplicationService
from app.identity_access.application.role_permission_application_service import RolePermissionApplicationService
from app.identity_access.application.identity_access_application_service import IdentityAccessApplicationService

# 从用户依赖模块导入基础依赖
from .user_deps import (
    get_user_repository, 
    get_role_repository, 
    get_login_history_repository,
    get_tenant_repository,
    get_permission_repository,
    get_user_domain_service,
    get_authentication_domain_service,
    get_permission_domain_service
)

logger = logging.getLogger(__name__)

# 获取配置
settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


# ==================== 服务依赖注入 ====================

def get_jwt_service() -> JWTService:
    """获取JWT服务实例"""
    return JWTService()


def get_security_domain_service(
    jwt_service: JWTService = Depends(get_jwt_service),
    user_repository = Depends(get_user_repository)
) -> SecurityDomainService:
    """获取安全领域服务实例"""
    return SecurityDomainService(user_repository, jwt_service)


def get_security_application_service(
    security_domain_service: SecurityDomainService = Depends(get_security_domain_service)
) -> SecurityApplicationService:
    """获取安全应用服务实例"""
    return SecurityApplicationService(security_domain_service)


# ==================== 新的权限服务依赖 ====================

def get_tenant_domain_service(
    tenant_repository = Depends(get_tenant_repository),
    user_repository = Depends(get_user_repository)
) -> TenantDomainService:
    """获取租户领域服务实例"""
    return TenantDomainService(tenant_repository, user_repository)


def get_role_permission_domain_service(
    role_repository = Depends(get_role_repository),
    permission_repository = Depends(get_permission_repository),
    user_repository = Depends(get_user_repository)
) -> RolePermissionDomainService:
    """获取角色权限领域服务实例"""
    return RolePermissionDomainService(role_repository, permission_repository, user_repository)


def get_tenant_application_service(
    tenant_domain_service: TenantDomainService = Depends(get_tenant_domain_service)
) -> TenantApplicationService:
    """获取租户应用服务实例"""
    return TenantApplicationService(tenant_domain_service)


def get_role_permission_application_service(
    role_permission_domain_service: RolePermissionDomainService = Depends(get_role_permission_domain_service)
) -> RolePermissionApplicationService:
    """获取角色权限应用服务实例"""
    return RolePermissionApplicationService(role_permission_domain_service)


def get_identity_access_application_service(
    user_repository = Depends(get_user_repository),
    role_repository = Depends(get_role_repository),
    login_history_repository = Depends(get_login_history_repository),
    user_domain_service = Depends(get_user_domain_service),
    authentication_domain_service = Depends(get_authentication_domain_service),
    permission_domain_service = Depends(get_permission_domain_service),
    tenant_domain_service: Optional[TenantDomainService] = Depends(get_tenant_domain_service),
    role_permission_domain_service: Optional[RolePermissionDomainService] = Depends(get_role_permission_domain_service)
) -> IdentityAccessApplicationService:
    """获取身份访问应用服务实例"""
    from app.identity_access.application.identity_access_application_service import IdentityAccessApplicationService
    return IdentityAccessApplicationService(
        user_repository=user_repository,
        role_repository=role_repository,
        login_history_repository=login_history_repository,
        user_domain_service=user_domain_service,
        authentication_domain_service=authentication_domain_service,
        permission_domain_service=permission_domain_service,
        tenant_domain_service=tenant_domain_service,
        role_permission_domain_service=role_permission_domain_service
    )


# ==================== 核心认证依赖 ====================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    security_app_service: SecurityApplicationService = Depends(get_security_application_service)
) -> User:
    """
    获取当前用户 - 核心认证依赖函数
    
    Args:
        token: JWT令牌
        security_app_service: 安全应用服务
        
    Returns:
        User: 认证成功的用户对象
        
    Raises:
        HTTPException: 如果认证失败或用户不存在
    """
    return await security_app_service.get_current_user(token)


async def get_current_admin(
    current_user: User = Depends(get_current_user),
    security_app_service: SecurityApplicationService = Depends(get_security_application_service)
) -> User:
    """
    获取当前管理员用户 - 管理员权限检查
    
    Args:
        current_user: 当前认证用户
        security_app_service: 安全应用服务
        
    Returns:
        User: 管理员用户对象
        
    Raises:
        HTTPException: 如果用户不是管理员
    """
    return await security_app_service.get_current_admin(current_user)


# ==================== 权限检查工具函数 ====================

def get_user_roles(user: User) -> List[str]:
    """获取用户角色列表"""
    logger.debug(f"get_user_roles开始获取用户角色 - user_id: {user.id}")
    logger.debug(f"user.roles类型: {type(user.roles)}, 内容: {user.roles}")
    
    if not user.roles:
        logger.debug(f"用户 {user.id} 没有角色")
        return []
    
    # user.roles 是一个 set 对象，需要安全地处理
    roles = []
    for i, role in enumerate(user.roles):
        try:
            logger.debug(f"处理第 {i+1} 个角色: {role}, 类型: {type(role)}")
            if hasattr(role, 'name'):
                role_name = role.name
                logger.debug(f"角色对象，名称: {role_name}")
                roles.append(role_name)
            else:
                # 如果是字符串类型的角色
                role_name = str(role)
                logger.debug(f"字符串角色: {role_name}")
                roles.append(role_name)
        except Exception as e:
            logger.error(f"处理第 {i+1} 个角色失败: {e}, 角色内容: {role}")
            import traceback
            logger.error(f"角色处理错误堆栈: {traceback.format_exc()}")
            continue
    
    logger.debug(f"用户 {user.id} 的角色: {roles}")
    return roles


def get_user_primary_role(user: User) -> str:
    """获取用户的主要角色（第一个角色）"""
    logger.debug(f"get_user_primary_role开始获取用户主要角色 - user_id: {user.id}")
    
    # 优先使用活跃角色
    if hasattr(user, '_active_role') and user._active_role:
        logger.debug(f"用户 {user.id} 有活跃角色: {user._active_role}")
        return user._active_role
    
    # 获取角色列表
    logger.debug(f"用户 {user.id} 没有活跃角色，获取角色列表")
    roles = get_user_roles(user)
    if roles:
        primary_role = roles[0]
        logger.debug(f"用户 {user.id} 的主要角色: {primary_role}")
        return primary_role
    
    # 默认角色
    logger.debug(f"用户 {user.id} 没有角色，使用默认角色: customer")
    return 'customer'


def check_user_has_role(user: User, role_name: str) -> bool:
    """检查用户是否有指定角色"""
    logger.debug(f"check_user_has_role开始检查用户角色 - user_id: {user.id}, role_name: {role_name}")
    
    try:
        # 安全地检查角色
        user_roles = get_user_roles(user)
        has_role = role_name in user_roles
        logger.debug(f"检查用户 {user.id} 是否有角色 {role_name}: {has_role}, 用户角色: {user_roles}")
        return has_role
    except Exception as e:
        logger.error(f"检查用户角色失败: {e}")
        import traceback
        logger.error(f"角色检查错误堆栈: {traceback.format_exc()}")
        return False


# ==================== 权限检查依赖函数 ====================

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


def check_role_permission(required_roles: Optional[List[str]] = None):
    """
    检查用户是否有所需角色的装饰器工厂函数
    
    Args:
        required_roles: 所需的角色列表
        
    Returns:
        函数: 检查用户角色的依赖函数
    """
    async def check_permission(
        current_user: User = Depends(get_current_user),
        security_app_service: SecurityApplicationService = Depends(get_security_application_service)
    ):
        """检查用户权限的依赖函数"""
        return await security_app_service.check_role_permission_use_case(current_user, required_roles)
    
    return check_permission


# ==================== 向后兼容函数 ====================

def verify_token(token: str) -> Optional[str]:
    """
    验证JWT令牌并提取用户ID - 向后兼容函数
    
    Args:
        token: JWT令牌
    
    Returns:
        str: 用户ID，如果令牌无效则返回None
    """
    jwt_service = JWTService()
    payload = jwt_service.verify_token(token)
    if payload:
        return payload.get("sub")
    return None


def create_access_token(
    subject, 
    expires_delta=None,
    active_role=None
) -> str:
    """
    创建访问令牌 - 向后兼容函数
    
    Args:
        subject: 令牌主体 (通常是用户ID)
        expires_delta: 过期时间增量
        active_role: 用户当前活跃角色
        
    Returns:
        str: JWT令牌
    """
    jwt_service = JWTService()
    return jwt_service.create_access_token(subject, expires_delta, active_role)


def create_refresh_token(
    subject,
    expires_delta=None,
    active_role=None
) -> str:
    """
    创建刷新令牌 - 向后兼容函数
    
    Args:
        subject: 令牌主体 (通常是用户ID)
        expires_delta: 过期时间增量
        active_role: 用户当前活跃角色
        
    Returns:
        str: JWT刷新令牌
    """
    jwt_service = JWTService()
    return jwt_service.create_refresh_token(subject, expires_delta, active_role)


# ==================== 导出所有依赖函数 ====================

__all__ = [
    # OAuth2配置
    "oauth2_scheme",
    
    # 服务依赖
    "get_jwt_service",
    "get_security_domain_service", 
    "get_security_application_service",
    
    # 核心认证
    "get_current_user",
    "get_current_admin",
    
    # 权限检查工具
    "get_user_roles",
    "check_user_has_role",
    
    # 权限检查依赖
    "require_role",
    "require_any_role",
    "check_role_permission",
    
    # 向后兼容函数
    "verify_token",
    "create_access_token",
    "create_refresh_token"
]
