"""
任务依赖注入模块
"""
from .tasks import get_task_application_service, get_task_domain_service, get_task_repository

__all__ = [
    "get_task_application_service",
    "get_task_domain_service", 
    "get_task_repository"
]
