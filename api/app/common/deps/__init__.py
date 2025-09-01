"""
依赖注入公共模块
- common: 通用依赖（数据库、基础服务）
"""

# 重新导出所有依赖，保持向后兼容
from .common import get_db

__all__ = [
    # 通用依赖
    "get_db",
]
