"""
依赖注入公共模块
- common: 通用依赖（数据库、基础服务）
"""

from .common import get_db, Base, SessionLocal, init_db

__all__ = [
    "get_db",
    "Base",
    "SessionLocal",
    "init_db",
]
