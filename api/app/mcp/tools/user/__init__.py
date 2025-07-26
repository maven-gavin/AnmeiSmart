"""
用户相关MCP工具模块

提供用户信息查询、搜索等功能
"""

from .profile import *
from .search import *

__all__ = ["get_user_profile", "search_users"] 