"""
任务服务模块 - 新架构
"""

# 导出控制器
from .controllers import tasks_router

# 导出模型
from .models import Task

# 导出服务
from .services import TaskService

__all__ = [
    "tasks_router",
    "Task",
    "TaskService",
]
