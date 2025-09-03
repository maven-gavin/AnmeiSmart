"""
身份访问模块依赖注入配置
"""
from .identity_access import (
    get_identity_access_application_service,
    get_user_repository,
    get_role_repository,
    get_identity_access_application_service_from_container
)

__all__ = [
    "get_identity_access_application_service",
    "get_user_repository",
    "get_role_repository",
    "get_identity_access_application_service_from_container"
]
