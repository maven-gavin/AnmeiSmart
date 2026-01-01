"""
身份访问模块依赖注入统一导出
- user_deps.py: 用户相关的服务依赖
- auth_deps.py: 认证授权相关的所有功能依赖
"""

# 从用户依赖模块导出
from .user_deps import (
    get_user_service,
    get_auth_service,
    get_role_service
)

# 从认证依赖模块导出
from .auth_deps import (
    # OAuth2配置
    oauth2_scheme,
    
    # 核心认证
    get_current_user,
    get_current_user_optional,
    get_current_admin,
    
    # 权限检查依赖
    require_role,
)

# 从权限依赖模块导出（如果存在）
try:
    from .permission_deps import (
        get_user_roles,
        get_user_primary_role,
        check_user_has_role,
        check_user_any_role,
        require_any_role,
        check_role_permission,
    )
except ImportError:
    # 如果 permission_deps 不存在或没有这些函数，定义占位符
    get_user_roles = None
    get_user_primary_role = None
    check_user_has_role = None
    check_user_any_role = None
    require_any_role = None
    check_role_permission = None


# 导出所有依赖函数
__all__ = [
    # 用户相关服务依赖
    "get_user_service",
    "get_auth_service",
    "get_role_service",
    
    # OAuth2配置
    "oauth2_scheme",
    
    # 核心认证
    "get_current_user",
    "get_current_user_optional",
    "get_current_admin",
    
    # 权限检查依赖
    "require_role",
]

# 有条件导出权限检查工具（如果存在）
if get_user_roles is not None:
    __all__.extend([
        "get_user_roles",
        "get_user_primary_role",
        "check_user_has_role",
        "check_user_any_role",
        "require_any_role",
        "check_role_permission",
    ])
