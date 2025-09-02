"""
身份访问模块数据库模型导出

导出该领域的所有数据库模型，确保SQLAlchemy可以正确建立关系映射。
"""

from .user import User, Role, Doctor, Consultant, Operator, Administrator
from .profile import UserPreferences, UserDefaultRole, LoginHistory

__all__ = [
    "User", "Role", "Doctor", "Consultant", "Operator", "Administrator",
    "UserPreferences", "UserDefaultRole", "LoginHistory"
]
