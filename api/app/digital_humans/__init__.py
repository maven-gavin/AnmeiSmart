"""
数字人服务模块 - 新架构
"""

# 导出控制器
from .controllers import digital_humans_router, admin_digital_humans_router

# 导出模型
from .models import DigitalHuman, DigitalHumanAgentConfig

# 导出服务
from .services import DigitalHumanService

__all__ = [
    "digital_humans_router",
    "admin_digital_humans_router",
    "DigitalHuman",
    "DigitalHumanAgentConfig",
    "DigitalHumanService",
]
