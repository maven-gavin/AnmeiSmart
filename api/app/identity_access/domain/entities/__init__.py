"""
实体定义 - 用户身份与权限上下文

实体是有身份的对象，通过唯一标识符来区分。
"""

from .user import UserEntity
from .role import RoleEntity
from .permission import PermissionEntity
from .tenant import TenantEntity
from .resource import ResourceEntity

__all__ = [
    "UserEntity",
    "RoleEntity",
    "PermissionEntity",
    "TenantEntity",
    "ResourceEntity"
]
