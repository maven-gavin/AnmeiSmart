"""
系统管理模块 - 新架构
"""

# 导出控制器
from .controllers import system_router

# 导出模型
from .models import SystemSettings

# 导出服务
from .services import SystemService

__all__ = [
    "system_router",
    "SystemSettings",
    "SystemService",
]
