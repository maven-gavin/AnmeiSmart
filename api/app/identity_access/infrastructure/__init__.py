"""
基础设施层 - 用户身份与权限上下文

包含数据访问、外部服务集成、技术实现。
"""

from .dependency_container import dependency_container
from .repositories.user_repository import UserRepository
from .repositories.role_repository import RoleRepository
from .repositories.login_history_repository import LoginHistoryRepository

__all__ = [
    "dependency_container",
    "UserRepository",
    "RoleRepository",
    "LoginHistoryRepository"
]
