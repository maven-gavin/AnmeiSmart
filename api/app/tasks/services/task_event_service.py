from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.tasks.models import TaskEvent
from app.tasks.schemas.task_event import TaskEventResponse


class TaskEventService:
    """任务事件服务（M1）"""

    def __init__(self, db: Session):
        self.db = db

    def create_event(
        self,
        *,
        task_id: str,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None,
    ) -> TaskEvent:
        event = TaskEvent(
            task_id=task_id,
            event_type=event_type,
            payload=payload,
            created_by=created_by,
        )
        self.db.add(event)
        self.db.flush()
        return event

    def list_events(self, task_id: str) -> List[TaskEventResponse]:
        events = (
            self.db.query(TaskEvent)
            .filter(TaskEvent.task_id == task_id)
            .order_by(TaskEvent.created_at.asc())
            .all()
        )
        return [
            TaskEventResponse(
                id=e.id,
                task_id=e.task_id,
                event_type=e.event_type,
                payload=e.payload,
                created_at=e.created_at,
                created_by=e.created_by,
            )
            for e in events
        ]


