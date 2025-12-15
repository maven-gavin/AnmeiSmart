import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.api import BusinessException, ErrorCode
from app.tasks.models import TaskQueue
from app.tasks.schemas.task_queue import CreateTaskQueueRequest, TaskQueueResponse, UpdateTaskQueueRequest

logger = logging.getLogger(__name__)


class TaskQueueService:
    """任务队列服务（M1）"""

    def __init__(self, db: Session):
        self.db = db

    def list_queues(self, scene_key: Optional[str] = None, only_active: bool = False) -> List[TaskQueueResponse]:
        query = self.db.query(TaskQueue)
        if scene_key:
            query = query.filter(TaskQueue.scene_key == scene_key)
        if only_active:
            query = query.filter(TaskQueue.is_active.is_(True))
        queues = query.order_by(TaskQueue.created_at.desc()).all()
        return [
            TaskQueueResponse(
                id=q.id,
                name=q.name,
                scene_key=q.scene_key,
                description=q.description,
                rotation_strategy=q.rotation_strategy,
                config=q.config,
                is_active=q.is_active,
                created_at=q.created_at,
                updated_at=q.updated_at,
            )
            for q in queues
        ]

    def get_by_id(self, queue_id: str) -> TaskQueue:
        queue = self.db.query(TaskQueue).filter(TaskQueue.id == queue_id).first()
        if not queue:
            raise BusinessException("队列不存在", code=ErrorCode.NOT_FOUND)
        return queue

    def get_by_name(self, name: str) -> Optional[TaskQueue]:
        return self.db.query(TaskQueue).filter(TaskQueue.name == name).first()

    def create_queue(self, data: CreateTaskQueueRequest) -> TaskQueueResponse:
        if self.get_by_name(data.name):
            raise BusinessException("队列名称已存在", code=ErrorCode.BUSINESS_ERROR)

        queue = TaskQueue(
            name=data.name,
            scene_key=data.scene_key,
            description=data.description,
            rotation_strategy=data.rotation_strategy,
            config=data.config,
            is_active=data.is_active,
        )
        self.db.add(queue)
        self.db.commit()
        self.db.refresh(queue)
        return TaskQueueResponse(
            id=queue.id,
            name=queue.name,
            scene_key=queue.scene_key,
            description=queue.description,
            rotation_strategy=queue.rotation_strategy,
            config=queue.config,
            is_active=queue.is_active,
            created_at=queue.created_at,
            updated_at=queue.updated_at,
        )

    def update_queue(self, queue_id: str, data: UpdateTaskQueueRequest) -> TaskQueueResponse:
        queue = self.get_by_id(queue_id)

        if data.name is not None and data.name != queue.name:
            if self.get_by_name(data.name):
                raise BusinessException("队列名称已存在", code=ErrorCode.BUSINESS_ERROR)
            queue.name = data.name
        if data.scene_key is not None:
            queue.scene_key = data.scene_key
        if data.description is not None:
            queue.description = data.description
        if data.rotation_strategy is not None:
            queue.rotation_strategy = data.rotation_strategy
        if data.config is not None:
            queue.config = data.config
        if data.is_active is not None:
            queue.is_active = data.is_active

        self.db.commit()
        self.db.refresh(queue)
        return TaskQueueResponse(
            id=queue.id,
            name=queue.name,
            scene_key=queue.scene_key,
            description=queue.description,
            rotation_strategy=queue.rotation_strategy,
            config=queue.config,
            is_active=queue.is_active,
            created_at=queue.created_at,
            updated_at=queue.updated_at,
        )

    def delete_queue(self, queue_id: str) -> None:
        queue = self.get_by_id(queue_id)
        self.db.delete(queue)
        self.db.commit()


