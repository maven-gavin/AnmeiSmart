"""
任务路由规则相关Schema（M1）
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaskRoutingRuleBase(BaseModel):
    """任务路由规则基础模型"""

    scene_key: str = Field(..., min_length=1, max_length=100, description="场景Key")
    keyword: str = Field(..., min_length=1, max_length=200, description="关键词/短语")
    match_type: str = Field("contains", description="匹配类型：contains/regex")
    priority: int = Field(100, ge=0, le=10_000, description="优先级（越小越优先）")
    target: Optional[str] = Field(None, max_length=200, description="目标（Agent/Workflow标识，M1占位）")
    task_templates: Optional[List[Dict[str, Any]]] = Field(None, description="命中后要生成的任务模板（JSON数组）")
    description: Optional[str] = Field(None, max_length=2000, description="规则说明")
    enabled: bool = Field(True, description="是否启用")


class CreateTaskRoutingRuleRequest(TaskRoutingRuleBase):
    """创建路由规则请求"""


class UpdateTaskRoutingRuleRequest(BaseModel):
    """更新路由规则请求"""

    scene_key: Optional[str] = Field(None, min_length=1, max_length=100)
    keyword: Optional[str] = Field(None, min_length=1, max_length=200)
    match_type: Optional[str] = Field(None, description="contains/regex")
    priority: Optional[int] = Field(None, ge=0, le=10_000)
    target: Optional[str] = Field(None, max_length=200)
    task_templates: Optional[List[Dict[str, Any]]] = None
    description: Optional[str] = Field(None, max_length=2000)
    enabled: Optional[bool] = None


class TaskRoutingRuleResponse(TaskRoutingRuleBase):
    """路由规则响应"""

    id: str
    created_at: datetime
    updated_at: datetime


