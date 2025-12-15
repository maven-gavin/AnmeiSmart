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
from app.tasks.services.task_queue_service import TaskQueueService
from app.tasks.services.task_routing_rule_service import TaskRoutingRuleService
from app.tasks.services.task_sensitive_rule_service import TaskSensitiveRuleService
from app.tasks.services.task_event_service import TaskEventService
from app.tasks.services.governed_task_center_service import GovernedTaskCenterService
from app.tasks.services.task_metrics_service import TaskMetricsService


def get_task_service(db: Session = Depends(get_db)) -> TaskService:
    """获取任务服务实例"""
    return TaskService(db)


def get_task_queue_service(db: Session = Depends(get_db)) -> TaskQueueService:
    return TaskQueueService(db)


def get_task_routing_rule_service(db: Session = Depends(get_db)) -> TaskRoutingRuleService:
    return TaskRoutingRuleService(db)


def get_task_sensitive_rule_service(db: Session = Depends(get_db)) -> TaskSensitiveRuleService:
    return TaskSensitiveRuleService(db)


def get_task_event_service(db: Session = Depends(get_db)) -> TaskEventService:
    return TaskEventService(db)


def get_governed_task_center_service(db: Session = Depends(get_db)) -> GovernedTaskCenterService:
    return GovernedTaskCenterService(db)


def get_task_metrics_service(db: Session = Depends(get_db)) -> TaskMetricsService:
    return TaskMetricsService(db)
