"""
身份访问模块依赖注入统一导出
- user_deps.py: 用户相关的仓储和应用服务依赖
- auth_deps.py: 认证授权相关的所有功能依赖
"""

# 从用户依赖模块导出
from .user_deps import (
    get_user_repository,
    get_role_repository,
    get_identity_access_application_service
)

# 从认证依赖模块导出
from .auth_deps import (
    # OAuth2配置
    oauth2_scheme,
    
    # 服务依赖
    get_jwt_service,
    get_security_domain_service,
    get_security_application_service,
    
    # 核心认证
    get_current_user,
    get_current_admin,
    
    # 权限检查工具
    get_user_roles,
    check_user_has_role,
    
    # 权限检查依赖
    require_role,
    require_any_role,
    check_role_permission,
    
    # 向后兼容函数
    verify_token,
    create_access_token,
    create_refresh_token
)


# 导出所有依赖函数
__all__ = [
    # 用户相关依赖
    "get_user_repository",
    "get_role_repository",
    "get_identity_access_application_service",
    
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
