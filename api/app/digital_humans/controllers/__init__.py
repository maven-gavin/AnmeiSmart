"""
数字人模块控制器导出
"""

from .digital_humans import router as digital_humans_router
from .admin_digital_humans import router as admin_digital_humans_router

__all__ = [
    "digital_humans_router",
    "admin_digital_humans_router",
]

