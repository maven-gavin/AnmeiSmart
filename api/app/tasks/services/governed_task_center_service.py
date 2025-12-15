from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.api import BusinessException, ErrorCode
from app.tasks.models import PendingTask, TaskQueue
from app.tasks.schemas.governed_route import RouteTaskRequest, RouteTaskResponse
from app.tasks.schemas.task import TaskResponse
from app.tasks.services.task_event_service import TaskEventService
from app.tasks.services.task_queue_service import TaskQueueService
from app.tasks.services.task_routing_rule_service import TaskRoutingRuleService
from app.tasks.services.task_sensitive_rule_service import TaskSensitiveRuleService


def _default_sensitive_suggestions(category: str) -> List[Dict[str, Any]]:
    if category == "pricing":
        return [
            {"title": "合规版回复", "text": "我先确认规格/数量/交期/付款条款后给您正式报价单（含税/不含税可选）。价格以正式报价为准。"},
            {"title": "引导补充信息", "text": "方便提供型号/数量/交期/收货地/付款方式吗？我们会据此给到准确报价与交期。"},
        ]
    if category == "commitment":
        return [
            {"title": "不承诺版", "text": "我先帮您确认出货节点与物流信息，并在X点前给您明确进展。为避免误差，先以确认后的节点为准。"},
            {"title": "方案版", "text": "如果您对交期非常紧，我们可以评估：先发部分/替代型号/加急排产（以内部确认结果为准）。"},
        ]
    if category == "confidential":
        return [
            {"title": "可公开资料", "text": "我先给您发送公开版本资料（产品手册/认证报告）。涉及图纸/工艺参数的内容需要走授权流程（如签署NDA）。"},
            {"title": "走流程版", "text": "涉及保密资料，我们可以先走资料申请/授权流程，授权后再提供对应文件。"},
        ]
    if category == "destructive":
        return [
            {"title": "安全处理", "text": "此类操作需要确认范围与审批人，请先发起工单确认后再执行，避免误删/误改。"},
        ]
    return [{"title": "安全建议", "text": "命中敏感规则，建议改写为更稳妥的表达或走流程确认后再执行。"}]


class GovernedTaskCenterService:
    """可治理任务中枢（M1）- 路由执行：scene+text → 生成任务/敏感拦截"""

    def __init__(self, db: Session):
        self.db = db
        self.queue_service = TaskQueueService(db)
        self.routing_service = TaskRoutingRuleService(db)
        self.sensitive_service = TaskSensitiveRuleService(db)
        self.event_service = TaskEventService(db)

    def _pick_queue(self, scene_key: str, queue_name: Optional[str] = None) -> Optional[TaskQueue]:
        if queue_name:
            q = self.db.query(TaskQueue).filter(TaskQueue.name == queue_name, TaskQueue.is_active.is_(True)).first()
            if q:
                return q
        return (
            self.db.query(TaskQueue)
            .filter(TaskQueue.scene_key == scene_key, TaskQueue.is_active.is_(True))
            .order_by(TaskQueue.created_at.desc())
            .first()
        )

    def _apply_assignment_from_queue(self, task: PendingTask, queue: Optional[TaskQueue]) -> None:
        if not queue:
            return
        if queue.rotation_strategy != "fixed":
            return
        config = queue.config or {}
        assignee_user_id = config.get("assignee_user_id")
        if assignee_user_id:
            task.assigned_to = assignee_user_id
            task.assigned_at = datetime.now()
            task.status = "assigned"

    def route_and_create_tasks(self, *, user_id: str, request: RouteTaskRequest) -> RouteTaskResponse:
        text = request.text.strip()
        if not text:
            raise BusinessException("文本不能为空", code=ErrorCode.INVALID_INPUT)

        # 1) 先做敏感检测（少数拦截）
        sensitive_hit = self.sensitive_service.detect(text)
        if sensitive_hit:
            rule, category = sensitive_hit
            suggestions = rule.suggestion_templates or _default_sensitive_suggestions(category)

            task = PendingTask(
                title=f"敏感拦截（{category}）",
                description="命中敏感规则，建议使用安全改写版本后再发送/再执行",
                task_type="sensitive_guard",
                priority="high",
                status="pending",
                created_by=user_id,
                task_data={
                    "scene_key": request.scene_key,
                    "text": text,
                    "category": category,
                    "matched_rule_id": rule.id,
                    "suggestions": suggestions,
                    "digital_human_id": request.digital_human_id,
                    "conversation_id": request.conversation_id,
                    "message_id": request.message_id,
                },
            )
            self.db.add(task)
            self.db.flush()
            self.event_service.create_event(
                task_id=task.id,
                event_type="created",
                payload={"route_type": "sensitive", "category": category, "matched_rule_id": rule.id},
                created_by=user_id,
            )
            self.db.commit()
            self.db.refresh(task)

            return RouteTaskResponse(
                route_type="sensitive",
                matched_sensitive_rule_id=rule.id,
                sensitive_category=category,
                suggestions=suggestions,
                created_tasks=[TaskResponse.from_model(task)],
            )

        # 2) 路由规则命中（场景+关键词）
        rule = self.routing_service.match_rule(request.scene_key, text)
        if not rule:
            if not request.create_fallback_task:
                return RouteTaskResponse(route_type="none", created_tasks=[])

            task = PendingTask(
                title="需要配置路由规则",
                description=f"场景={request.scene_key} 未命中关键词规则，请管理员配置路由与任务模板",
                task_type="routing_config_required",
                priority="medium",
                status="pending",
                created_by=user_id,
                task_data={
                    "scene_key": request.scene_key,
                    "text": text,
                    "digital_human_id": request.digital_human_id,
                    "conversation_id": request.conversation_id,
                    "message_id": request.message_id,
                },
            )
            self.db.add(task)
            self.db.flush()
            self.event_service.create_event(task_id=task.id, event_type="created", payload={"route_type": "none"}, created_by=user_id)
            self.db.commit()
            self.db.refresh(task)
            return RouteTaskResponse(route_type="none", created_tasks=[TaskResponse.from_model(task)])

        templates: List[Dict[str, Any]] = list(rule.task_templates or [])
        created: List[PendingTask] = []
        now = datetime.now()

        for t in templates:
            task_type = str(t.get("task_type") or t.get("type") or "").strip()
            if not task_type:
                continue

            title = str(t.get("title") or "").strip() or f"{request.scene_key}:{task_type}"
            description = t.get("description")
            priority = str(t.get("priority") or "medium")

            due_in_minutes = t.get("due_in_minutes")
            due_date = None
            if isinstance(due_in_minutes, int) and due_in_minutes > 0:
                due_date = now + timedelta(minutes=due_in_minutes)

            queue_name = t.get("queue_name")
            queue = self._pick_queue(request.scene_key, queue_name=queue_name)

            task = PendingTask(
                title=title,
                description=description,
                task_type=task_type,
                priority=priority,
                status="pending",
                created_by=user_id,
                due_date=due_date,
                task_data={
                    "scene_key": request.scene_key,
                    "trigger_text": text,
                    "matched_rule_id": rule.id,
                    "template": t,
                    "queue_name": queue.name if queue else None,
                    "digital_human_id": request.digital_human_id,
                    "conversation_id": request.conversation_id,
                    "message_id": request.message_id,
                },
            )
            self._apply_assignment_from_queue(task, queue)

            self.db.add(task)
            self.db.flush()
            self.event_service.create_event(
                task_id=task.id,
                event_type="created",
                payload={"route_type": "routing", "matched_rule_id": rule.id, "task_type": task_type},
                created_by=user_id,
            )
            if task.status == "assigned" and task.assigned_to:
                self.event_service.create_event(
                    task_id=task.id,
                    event_type="assigned",
                    payload={"assigned_to": task.assigned_to, "queue": queue.name if queue else None},
                    created_by=user_id,
                )
            created.append(task)

        self.db.commit()
        for t in created:
            self.db.refresh(t)

        return RouteTaskResponse(
            route_type="routing",
            matched_rule_id=rule.id,
            created_tasks=[TaskResponse.from_model(t) for t in created],
        )


