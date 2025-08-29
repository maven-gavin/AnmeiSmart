"""
通用依赖模块 - 数据库、基础服务等
"""
from app.db.base import get_db

__all__ = ["get_db"]
