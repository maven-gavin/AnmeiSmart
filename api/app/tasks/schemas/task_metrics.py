"""
任务治理指标 Schema（M4）
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TaskGovernanceSceneMetrics(BaseModel):
    scene_key: str = Field(..., description="场景Key")

    tasks_created: int = Field(..., ge=0, description="期间创建任务数")
    tasks_completed: int = Field(..., ge=0, description="期间完成任务数（按 completed_at）")

    routing_tasks_created: int = Field(..., ge=0, description="路由生成任务数（非敏感/非需要配置）")
    sensitive_tasks_created: int = Field(..., ge=0, description="敏感拦截任务数")
    config_required_tasks_created: int = Field(..., ge=0, description="需要配置任务数")

    overdue_open_tasks: int = Field(..., ge=0, description="已超期且未完成任务数（当前时刻）")

    sla_tasks_total: int = Field(..., ge=0, description="有 due_date 的已完成任务数")
    sla_tasks_on_time: int = Field(..., ge=0, description="有 due_date 的已完成任务中按时完成数")

    median_cycle_time_minutes: Optional[float] = Field(None, ge=0, description="完成中位耗时（分钟）")
    avg_cycle_time_minutes: Optional[float] = Field(None, ge=0, description="完成平均耗时（分钟）")


class TaskGovernanceMetricsResponse(BaseModel):
    start_at: datetime = Field(..., description="统计起始时间（含）")
    end_at: datetime = Field(..., description="统计结束时间（不含）")
    scene_key: Optional[str] = Field(None, description="筛选场景Key（可选）")

    tasks_created: int = Field(..., ge=0, description="期间创建任务数")
    tasks_completed: int = Field(..., ge=0, description="期间完成任务数（按 completed_at）")

    routing_tasks_created: int = Field(..., ge=0, description="路由生成任务数（非敏感/非需要配置）")
    sensitive_tasks_created: int = Field(..., ge=0, description="敏感拦截任务数")
    config_required_tasks_created: int = Field(..., ge=0, description="需要配置任务数")

    overdue_open_tasks: int = Field(..., ge=0, description="已超期且未完成任务数（当前时刻）")

    sla_tasks_total: int = Field(..., ge=0, description="有 due_date 的已完成任务数")
    sla_tasks_on_time: int = Field(..., ge=0, description="有 due_date 的已完成任务中按时完成数")

    median_cycle_time_minutes: Optional[float] = Field(None, ge=0, description="完成中位耗时（分钟）")
    avg_cycle_time_minutes: Optional[float] = Field(None, ge=0, description="完成平均耗时（分钟）")

    scenes: List[TaskGovernanceSceneMetrics] = Field(default_factory=list, description="按场景聚合明细")


