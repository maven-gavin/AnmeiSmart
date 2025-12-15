from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.tasks.models.task import PendingTask
from app.tasks.schemas.task_metrics import (
    TaskGovernanceMetricsResponse,
    TaskGovernanceSceneMetrics,
)


@dataclass(frozen=True)
class _Agg:
    tasks_created: int = 0
    tasks_completed: int = 0
    routing_tasks_created: int = 0
    sensitive_tasks_created: int = 0
    config_required_tasks_created: int = 0
    overdue_open_tasks: int = 0
    sla_tasks_total: int = 0
    sla_tasks_on_time: int = 0
    median_cycle_time_minutes: Optional[float] = None
    avg_cycle_time_minutes: Optional[float] = None


def _safe_scene_key(task: PendingTask) -> str:
    data = task.task_data or {}
    scene_key = data.get("scene_key")
    if isinstance(scene_key, str) and scene_key.strip():
        return scene_key.strip()
    return "unknown"


def _percentile_50(values: List[float]) -> Optional[float]:
    if not values:
        return None
    values.sort()
    mid = len(values) // 2
    if len(values) % 2 == 1:
        return values[mid]
    return (values[mid - 1] + values[mid]) / 2.0


class TaskMetricsService:
    """任务治理指标服务（M4）"""

    def __init__(self, db: Session):
        self.db = db

    def get_governance_metrics(
        self,
        *,
        start_at: datetime,
        end_at: datetime,
        scene_key: Optional[str] = None,
    ) -> TaskGovernanceMetricsResponse:
        # 统一时间为 UTC（避免时区差异导致边界错位）
        if start_at.tzinfo is None:
            start_at = start_at.replace(tzinfo=timezone.utc)
        if end_at.tzinfo is None:
            end_at = end_at.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)

        # 1) 取期间创建的任务（用于 created 口径）
        created_tasks: List[PendingTask] = (
            self.db.query(PendingTask)
            .filter(PendingTask.created_at >= start_at, PendingTask.created_at < end_at)
            .all()
        )

        # 2) 取期间完成的任务（用于 cycle_time / SLA 口径）
        completed_tasks: List[PendingTask] = (
            self.db.query(PendingTask)
            .filter(PendingTask.completed_at.isnot(None))
            .filter(PendingTask.completed_at >= start_at, PendingTask.completed_at < end_at)
            .all()
        )

        # 3) 为了计算超期未完成（当前时刻），取有 due_date 且未完成的任务
        open_overdue_tasks: List[PendingTask] = (
            self.db.query(PendingTask)
            .filter(PendingTask.due_date.isnot(None))
            .filter(PendingTask.status.in_(["pending", "assigned", "in_progress"]))
            .filter(PendingTask.due_date < now)
            .all()
        )

        if scene_key:
            created_tasks = [t for t in created_tasks if _safe_scene_key(t) == scene_key]
            completed_tasks = [t for t in completed_tasks if _safe_scene_key(t) == scene_key]
            open_overdue_tasks = [t for t in open_overdue_tasks if _safe_scene_key(t) == scene_key]

        # 聚合：按 scene_key 分桶
        by_scene_created: Dict[str, List[PendingTask]] = {}
        for t in created_tasks:
            by_scene_created.setdefault(_safe_scene_key(t), []).append(t)

        by_scene_completed: Dict[str, List[PendingTask]] = {}
        for t in completed_tasks:
            by_scene_completed.setdefault(_safe_scene_key(t), []).append(t)

        by_scene_overdue: Dict[str, List[PendingTask]] = {}
        for t in open_overdue_tasks:
            by_scene_overdue.setdefault(_safe_scene_key(t), []).append(t)

        scenes: List[TaskGovernanceSceneMetrics] = []
        all_scene_keys = sorted(set(by_scene_created.keys()) | set(by_scene_completed.keys()) | set(by_scene_overdue.keys()))

        totals_created = 0
        totals_completed = 0
        totals_routing = 0
        totals_sensitive = 0
        totals_config_required = 0
        totals_overdue = 0
        totals_sla_total = 0
        totals_sla_on_time = 0
        all_cycle_minutes: List[float] = []

        for sk in all_scene_keys:
            cts = by_scene_created.get(sk, [])
            dts = by_scene_completed.get(sk, [])
            ots = by_scene_overdue.get(sk, [])

            tasks_created = len(cts)
            tasks_completed = len(dts)

            sensitive_tasks_created = sum(1 for t in cts if t.task_type == "sensitive_guard")
            config_required_tasks_created = sum(1 for t in cts if t.task_type == "routing_config_required")
            routing_tasks_created = tasks_created - sensitive_tasks_created - config_required_tasks_created

            overdue_open_tasks = len(ots)

            cycle_minutes: List[float] = []
            sla_tasks_total = 0
            sla_tasks_on_time = 0
            for t in dts:
                if t.created_at and t.completed_at:
                    delta = (t.completed_at - t.created_at).total_seconds() / 60.0
                    if delta >= 0:
                        cycle_minutes.append(delta)
                        all_cycle_minutes.append(delta)
                if t.due_date is not None:
                    sla_tasks_total += 1
                    if t.completed_at is not None and t.completed_at <= t.due_date:
                        sla_tasks_on_time += 1

            avg_cycle = (sum(cycle_minutes) / len(cycle_minutes)) if cycle_minutes else None
            median_cycle = _percentile_50(cycle_minutes) if cycle_minutes else None

            scenes.append(
                TaskGovernanceSceneMetrics(
                    scene_key=sk,
                    tasks_created=tasks_created,
                    tasks_completed=tasks_completed,
                    routing_tasks_created=routing_tasks_created,
                    sensitive_tasks_created=sensitive_tasks_created,
                    config_required_tasks_created=config_required_tasks_created,
                    overdue_open_tasks=overdue_open_tasks,
                    sla_tasks_total=sla_tasks_total,
                    sla_tasks_on_time=sla_tasks_on_time,
                    median_cycle_time_minutes=median_cycle,
                    avg_cycle_time_minutes=avg_cycle,
                )
            )

            totals_created += tasks_created
            totals_completed += tasks_completed
            totals_routing += routing_tasks_created
            totals_sensitive += sensitive_tasks_created
            totals_config_required += config_required_tasks_created
            totals_overdue += overdue_open_tasks
            totals_sla_total += sla_tasks_total
            totals_sla_on_time += sla_tasks_on_time

        avg_all = (sum(all_cycle_minutes) / len(all_cycle_minutes)) if all_cycle_minutes else None
        median_all = _percentile_50(all_cycle_minutes) if all_cycle_minutes else None

        return TaskGovernanceMetricsResponse(
            start_at=start_at,
            end_at=end_at,
            scene_key=scene_key,
            tasks_created=totals_created,
            tasks_completed=totals_completed,
            routing_tasks_created=totals_routing,
            sensitive_tasks_created=totals_sensitive,
            config_required_tasks_created=totals_config_required,
            overdue_open_tasks=totals_overdue,
            sla_tasks_total=totals_sla_total,
            sla_tasks_on_time=totals_sla_on_time,
            median_cycle_time_minutes=median_all,
            avg_cycle_time_minutes=avg_all,
            scenes=scenes,
        )


