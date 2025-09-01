"""
领域层 - 用户身份与权限上下文

包含核心业务逻辑、领域规则、聚合设计。
"""

from .entities.user import User
from .entities.role import Role
from .value_objects.email import Email
from .value_objects.password import Password
from .value_objects.user_status import UserStatus
from .value_objects.role_type import RoleType
from .value_objects.login_history import LoginHistory
from .value_objects.admin_level import AdminLevel
from .user_domain_service import UserDomainService
from .authentication_domain_service import AuthenticationDomainService
from .permission_domain_service import PermissionDomainService

__all__ = [
    # 聚合根和实体
    "User",
    "Role",
    
    # 值对象
    "Email",
    "Password",
    "UserStatus",
    "RoleType",
    "LoginHistory",
    "AdminLevel",
    
    # 领域服务
    "UserDomainService",
    "AuthenticationDomainService",
    "PermissionDomainService"
]
