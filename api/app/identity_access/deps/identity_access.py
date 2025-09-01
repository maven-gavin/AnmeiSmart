"""
用户身份与权限上下文依赖注入配置

管理领域服务的依赖关系，提供接口实现。
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.infrastructure.db.base import get_db
from app.identity_access.infrastructure.repositories import (
    UserRepository,
    RoleRepository,
    LoginHistoryRepository
)
from app.identity_access.domain import (
    UserDomainService,
    AuthenticationDomainService,
    PermissionDomainService
)
from app.identity_access.application import IdentityAccessApplicationService


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """获取用户仓储实例"""
    return UserRepository(db)


def get_role_repository(db: Session = Depends(get_db)) -> RoleRepository:
    """获取角色仓储实例"""
    return RoleRepository(db)


def get_login_history_repository(db: Session = Depends(get_db)) -> LoginHistoryRepository:
    """获取登录历史仓储实例"""
    return LoginHistoryRepository(db)





def get_user_domain_service(
    user_repository: UserRepository = Depends(get_user_repository),
    role_repository: RoleRepository = Depends(get_role_repository)
) -> UserDomainService:
    """获取用户领域服务实例"""
    return UserDomainService(user_repository, role_repository)


def get_authentication_domain_service(
    user_repository: UserRepository = Depends(get_user_repository),
    login_history_repository: LoginHistoryRepository = Depends(get_login_history_repository)
) -> AuthenticationDomainService:
    """获取认证领域服务实例"""
    return AuthenticationDomainService(user_repository, login_history_repository)


def get_permission_domain_service(
    user_repository: UserRepository = Depends(get_user_repository)
) -> PermissionDomainService:
    """获取权限领域服务实例"""
    return PermissionDomainService(user_repository)


def get_identity_access_application_service(
    user_repository: UserRepository = Depends(get_user_repository),
    role_repository: RoleRepository = Depends(get_role_repository),
    login_history_repository: LoginHistoryRepository = Depends(get_login_history_repository),
    user_domain_service: UserDomainService = Depends(get_user_domain_service),
    authentication_domain_service: AuthenticationDomainService = Depends(get_authentication_domain_service),
    permission_domain_service: PermissionDomainService = Depends(get_permission_domain_service)
) -> IdentityAccessApplicationService:
    """获取用户身份与权限应用服务实例"""
    return IdentityAccessApplicationService(
        user_repository=user_repository,
        role_repository=role_repository,
        login_history_repository=login_history_repository,
        user_domain_service=user_domain_service,
        authentication_domain_service=authentication_domain_service,
        permission_domain_service=permission_domain_service
    )
