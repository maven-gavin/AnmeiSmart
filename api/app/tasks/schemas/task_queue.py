"""
任务队列相关Schema（M1）
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class TaskQueueBase(BaseModel):
    """任务队列基础模型"""

    name: str = Field(..., min_length=1, max_length=200, description="队列名称")
    scene_key: str = Field(..., min_length=1, max_length=100, description="场景Key")
    description: Optional[str] = Field(None, max_length=2000, description="队列描述")
    rotation_strategy: str = Field("fixed", description="分配策略：fixed/round_robin")
    config: Optional[Dict[str, Any]] = Field(None, description="队列配置（JSON）")
    is_active: bool = Field(True, description="是否启用")


class CreateTaskQueueRequest(TaskQueueBase):
    """创建任务队列请求"""


class UpdateTaskQueueRequest(BaseModel):
    """更新任务队列请求"""

    name: Optional[str] = Field(None, min_length=1, max_length=200, description="队列名称")
    scene_key: Optional[str] = Field(None, min_length=1, max_length=100, description="场景Key")
    description: Optional[str] = Field(None, max_length=2000, description="队列描述")
    rotation_strategy: Optional[str] = Field(None, description="分配策略：fixed/round_robin")
    config: Optional[Dict[str, Any]] = Field(None, description="队列配置（JSON）")
    is_active: Optional[bool] = Field(None, description="是否启用")


class TaskQueueResponse(TaskQueueBase):
    """任务队列响应"""

    id: str
    created_at: datetime
    updated_at: datetime


