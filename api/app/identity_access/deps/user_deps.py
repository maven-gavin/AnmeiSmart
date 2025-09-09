"""
用户相关依赖注入配置

遵循 @ddd_service_schema.mdc 第3章依赖注入配置规范：
- 使用FastAPI的依赖注入避免循环依赖
- 接口抽象：使用抽象接口而不是具体实现
- 依赖方向：确保依赖方向指向领域层
- 生命周期管理：合理管理依赖的作用域
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.deps import get_db
from app.identity_access.infrastructure.repositories.user_repository import UserRepository
from app.identity_access.infrastructure.repositories.role_repository import RoleRepository
from app.identity_access.application.identity_access_application_service import IdentityAccessApplicationService
from app.identity_access.converters.user_converter import UserConverter
from app.identity_access.converters.role_converter import RoleConverter
from app.identity_access.infrastructure.repositories.login_history_repository import LoginHistoryRepository
from app.identity_access.infrastructure.repositories.tenant_repository import TenantRepository
from app.identity_access.infrastructure.repositories.permission_repository import PermissionRepository
from app.identity_access.interfaces.domain_service_interfaces import IUserDomainService
from app.identity_access.interfaces.domain_service_interfaces import IAuthenticationDomainService
from app.identity_access.interfaces.domain_service_interfaces import IPermissionDomainService
from app.identity_access.domain.user_domain_service import UserDomainService
from app.identity_access.domain.authentication_domain_service import AuthenticationDomainService
from app.identity_access.domain.permission_domain_service import PermissionDomainService

def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """获取用户仓储实例"""
    return UserRepository(db, UserConverter())


def get_role_repository(db: Session = Depends(get_db)) -> RoleRepository:
    """获取角色仓储实例"""
    return RoleRepository(db, RoleConverter())


def get_login_history_repository(db: Session = Depends(get_db)) -> LoginHistoryRepository:
    """获取登录历史仓储实例"""
    return LoginHistoryRepository(db)


def get_tenant_repository(db: Session = Depends(get_db)) -> TenantRepository:
    """获取租户仓储实例"""
    return TenantRepository(db)


def get_permission_repository(db: Session = Depends(get_db)) -> PermissionRepository:
    """获取权限仓储实例"""
    return PermissionRepository(db)

def get_user_domain_service(
    user_repository: UserRepository = Depends(get_user_repository),
    role_repository: RoleRepository = Depends(get_role_repository)
) -> IUserDomainService:
    """获取用户领域服务实例"""
    return UserDomainService(user_repository, role_repository)

def get_authentication_domain_service(user_repository: UserRepository = Depends(get_user_repository), login_history_repository: LoginHistoryRepository = Depends(get_login_history_repository)) -> IAuthenticationDomainService:
    """获取认证领域服务实例"""
    return AuthenticationDomainService(user_repository, login_history_repository)

def get_permission_domain_service(user_repository: UserRepository = Depends(get_user_repository)) -> IPermissionDomainService:
    """获取权限领域服务实例"""
    return PermissionDomainService(user_repository)

def get_identity_access_application_service(
    user_repository: UserRepository = Depends(get_user_repository),
    role_repository: RoleRepository = Depends(get_role_repository),
    login_history_repository: LoginHistoryRepository = Depends(get_login_history_repository),
    user_domain_service: IUserDomainService = Depends(get_user_domain_service),
    authentication_domain_service: IAuthenticationDomainService = Depends(get_authentication_domain_service),
    permission_domain_service: IPermissionDomainService = Depends(get_permission_domain_service)
) -> IdentityAccessApplicationService:
    """获取身份访问应用服务实例"""
    return IdentityAccessApplicationService(
        user_repository=user_repository,
        role_repository=role_repository,
        login_history_repository=login_history_repository,
        user_domain_service=user_domain_service,
        authentication_domain_service=authentication_domain_service,
        permission_domain_service=permission_domain_service
    )


# 导出所有依赖函数
__all__ = [
    "get_user_repository",
    "get_role_repository", 
    "get_login_history_repository",
    "get_user_domain_service",
    "get_authentication_domain_service",
    "get_permission_domain_service",
    "get_identity_access_application_service"
]
