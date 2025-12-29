"""
可治理任务中枢：路由执行相关Schema（M1）
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.tasks.schemas.task import TaskResponse


class RouteTaskRequest(BaseModel):
    """路由执行请求：输入场景与文本，输出创建的任务（或敏感拦截）"""

    # Copilot 模式：scene_key 可为空，由路由器自动识别意图并选择 scene_key
    scene_key: Optional[str] = Field(None, min_length=1, max_length=100, description="场景Key（可选，留空=自动识别）")
    text: str = Field(..., min_length=1, max_length=5000, description="触发文本")

    digital_human_id: Optional[str] = Field(None, description="数字人ID（可选）")
    conversation_id: Optional[str] = Field(None, description="会话ID（可选）")
    message_id: Optional[str] = Field(None, description="消息ID（可选）")

    create_fallback_task: bool = Field(True, description="路由未命中时是否创建“需要配置”的任务")


class RouteTaskResponse(BaseModel):
    """路由执行响应"""

    route_type: str = Field(..., description="routing/sensitive/none")
    matched_rule_id: Optional[str] = Field(None, description="命中的路由规则ID（若有）")
    matched_sensitive_rule_id: Optional[str] = Field(None, description="命中的敏感规则ID（若有）")
    sensitive_category: Optional[str] = Field(None, description="敏感分类（若有）")
    suggestions: Optional[List[Dict[str, Any]]] = Field(None, description="敏感改写建议（若有）")

    created_tasks: List[TaskResponse] = Field(default_factory=list, description="创建的任务列表")


