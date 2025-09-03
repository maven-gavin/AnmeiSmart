"""
任务模块依赖注入配置

遵循 @ddd_service_schema.mdc 第3章依赖注入配置规范：
- 使用FastAPI的依赖注入避免循环依赖
- 接口抽象：使用抽象接口而不是具体实现
- 依赖方向：确保依赖方向指向领域层
- 生命周期管理：合理管理依赖的作用域
"""

from typing import Optional
from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.deps import get_db
from app.tasks.domain.interfaces import ITaskRepository, ITaskDomainService
from app.tasks.infrastructure.repositories.task_repository import TaskRepository
from app.tasks.domain.task_domain_service import TaskDomainService
from app.tasks.application.task_application_service import TaskApplicationService


def get_task_repository(db: Session = Depends(get_db)) -> TaskRepository:
    """获取任务仓储实例
    
    遵循DDD规范：
    - 使用FastAPI的依赖注入避免循环依赖
    - 依赖方向：确保依赖方向指向领域层
    """
    return TaskRepository(db)


def get_task_domain_service(
    task_repository: TaskRepository = Depends(get_task_repository)
) -> TaskDomainService:
    """获取任务领域服务实例
    
    遵循DDD规范：
    - 接口抽象：使用抽象接口而不是具体实现
    - 依赖方向：确保依赖方向指向领域层
    """
    return TaskDomainService(task_repository)


def get_task_application_service(
    task_domain_service: TaskDomainService = Depends(get_task_domain_service)
) -> TaskApplicationService:
    """获取任务应用服务实例
    
    遵循DDD规范：
    - 编排领域服务，实现用例，事务管理
    - 无状态，协调领域对象完成业务用例
    """
    return TaskApplicationService(task_domain_service)
