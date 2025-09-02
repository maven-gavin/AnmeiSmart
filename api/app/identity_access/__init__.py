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

from .application.identity_access_application_service import IdentityAccessApplicationService
from .application.security_application_service import SecurityApplicationService
from .domain.security_domain_service import SecurityDomainService
from .infrastructure.jwt_service import JWTService
from .converters.user_converter import UserConverter
from .converters.role_converter import RoleConverter

__all__ = [
    "IdentityAccessApplicationService",
    "SecurityApplicationService",
    "SecurityDomainService", 
    "JWTService",
    "UserConverter", 
    "RoleConverter"
]
