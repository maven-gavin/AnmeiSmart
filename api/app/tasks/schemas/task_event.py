"""
任务事件流水Schema（M1）
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class TaskEventResponse(BaseModel):
    """任务事件响应"""

    id: str
    task_id: str = Field(..., description="任务ID")
    event_type: str = Field(..., description="事件类型")
    payload: Optional[Dict[str, Any]] = Field(None, description="事件载荷")
    created_at: datetime
    created_by: Optional[str] = Field(None, description="创建人ID（若有）")


