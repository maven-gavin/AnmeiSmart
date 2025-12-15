"""
敏感规则相关Schema（M1）
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaskSensitiveRuleBase(BaseModel):
    """敏感规则基础模型"""

    category: str = Field(..., description="敏感分类：pricing/commitment/confidential/destructive")
    pattern: str = Field(..., min_length=1, max_length=300, description="匹配模式")
    match_type: str = Field("contains", description="匹配类型：contains/regex")
    priority: int = Field(100, ge=0, le=10_000, description="优先级（越小越优先）")
    suggestion_templates: Optional[List[Dict[str, Any]]] = Field(None, description="安全改写建议模板（JSON数组）")
    description: Optional[str] = Field(None, max_length=2000, description="规则说明")
    enabled: bool = Field(True, description="是否启用")


class CreateTaskSensitiveRuleRequest(TaskSensitiveRuleBase):
    """创建敏感规则请求"""


class UpdateTaskSensitiveRuleRequest(BaseModel):
    """更新敏感规则请求"""

    category: Optional[str] = None
    pattern: Optional[str] = Field(None, min_length=1, max_length=300)
    match_type: Optional[str] = Field(None, description="contains/regex")
    priority: Optional[int] = Field(None, ge=0, le=10_000)
    suggestion_templates: Optional[List[Dict[str, Any]]] = None
    description: Optional[str] = Field(None, max_length=2000)
    enabled: Optional[bool] = None


class TaskSensitiveRuleResponse(TaskSensitiveRuleBase):
    """敏感规则响应"""

    id: str
    created_at: datetime
    updated_at: datetime


