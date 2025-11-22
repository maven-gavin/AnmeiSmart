"""
任务模块依赖注入配置

遵循新架构标准：
- 使用FastAPI的依赖注入避免循环依赖
- 直接使用Service层，无需Repository抽象
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.deps import get_db
from app.tasks.services.task_service import TaskService


def get_task_service(db: Session = Depends(get_db)) -> TaskService:
    """获取任务服务实例"""
    return TaskService(db)
