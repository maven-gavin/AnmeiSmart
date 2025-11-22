"""
通用依赖模块 - 数据库、基础服务等
"""
from app.common.deps.database import get_db, Base, SessionLocal, init_db

__all__ = ["get_db", "Base", "SessionLocal", "init_db"]
