"""
值对象定义 - 用户身份与权限上下文

值对象是无身份的对象，通过属性值来标识。
"""

from .email import Email
from .password import Password
from .user_status import UserStatus
from .role_type import RoleType
from .login_history import LoginHistory
from .admin_level import AdminLevel
from .permission_type import PermissionType
from .permission_scope import PermissionScope
from .resource_type import ResourceType

__all__ = [
    "Email",
    "Password", 
    "UserStatus",
    "RoleType",
    "LoginHistory",
    "AdminLevel",
    "PermissionType",
    "PermissionScope",
    "ResourceType"
]
