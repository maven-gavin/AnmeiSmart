"""
身份访问模块依赖注入统一入口

提供所有依赖注入函数的统一导入点，遵循DDD分层架构。
"""

# 从核心依赖模块导入基础依赖
from .identity_access import (
    get_user_repository,
    get_role_repository,
    get_login_history_repository,
    get_user_domain_service,
    get_authentication_domain_service,
    get_permission_domain_service,
    get_identity_access_application_service
)

# 从安全依赖模块导入安全相关依赖
from .security_deps import (
    oauth2_scheme,
    get_jwt_service,
    get_security_domain_service,
    get_security_application_service,
    get_current_user,
    check_role_permission,
    get_current_admin,
    verify_token,
    create_access_token,
    create_refresh_token
)

# 从认证依赖模块导入权限检查工具
from .auth import (
    require_admin_role,
    get_user_roles,
    check_user_has_role,
    require_role,
    require_any_role
)

# 统一导出所有依赖函数
__all__ = [
    # 基础依赖
    "get_user_repository",
    "get_role_repository", 
    "get_login_history_repository",
    "get_user_domain_service",
    "get_authentication_domain_service",
    "get_permission_domain_service",
    "get_identity_access_application_service",
    
    # 安全依赖
    "oauth2_scheme",
    "get_jwt_service",
    "get_security_domain_service",
    "get_security_application_service",
    "get_current_user",
    "check_role_permission",
    "get_current_admin",
    "verify_token",
    "create_access_token",
    "create_refresh_token",
    
    # 权限检查工具
    "require_admin_role",
    "get_user_roles",
    "check_user_has_role",
    "require_role",
    "require_any_role"
]
