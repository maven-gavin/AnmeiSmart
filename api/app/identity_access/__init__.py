"""
用户身份与权限上下文 (Identity & Access Management)

本模块实现用户身份认证、角色权限管理、登录历史追踪等核心功能。
遵循DDD分层架构，提供清晰的业务边界和职责分离。

主要组件：
- 用户聚合根：管理用户身份和基本信息
- 角色实体：定义系统角色和权限
- 认证服务：处理用户登录和令牌管理
- 权限服务：验证用户访问权限
- 安全服务：处理JWT令牌和权限验证
"""

# 延迟导入避免循环依赖
__all__ = [
    "IdentityAccessApplicationService",
    "SecurityApplicationService",
    "SecurityDomainService", 
    "JWTService",
    "UserConverter", 
    "RoleConverter"
]

def __getattr__(name):
    """延迟导入避免循环依赖"""
    if name == "IdentityAccessApplicationService":
        from .application.identity_access_application_service import IdentityAccessApplicationService
        return IdentityAccessApplicationService
    elif name == "SecurityApplicationService":
        from .application.security_application_service import SecurityApplicationService
        return SecurityApplicationService
    elif name == "SecurityDomainService":
        from .domain.security_domain_service import SecurityDomainService
        return SecurityDomainService
    elif name == "JWTService":
        from .infrastructure.jwt_service import JWTService
        return JWTService
    elif name == "UserConverter":
        from .converters.user_converter import UserConverter
        return UserConverter
    elif name == "RoleConverter":
        from .converters.role_converter import RoleConverter
        return RoleConverter
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
