"""
待办任务管理API端点
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, status, Query

from app.identity_access.deps import get_current_user, get_user_primary_role
from app.identity_access.models.user import User
from app.core.api import ApiResponse, BusinessException, ErrorCode, SystemException
from app.tasks.schemas.task import (
    TaskResponse,
    CreateTaskRequest,
    UpdateTaskRequest,
)
from app.tasks.schemas.task_queue import CreateTaskQueueRequest, TaskQueueResponse, UpdateTaskQueueRequest
from app.tasks.schemas.routing_rule import (
    CreateTaskRoutingRuleRequest,
    TaskRoutingRuleResponse,
    UpdateTaskRoutingRuleRequest,
)
from app.tasks.schemas.sensitive_rule import (
    CreateTaskSensitiveRuleRequest,
    TaskSensitiveRuleResponse,
    UpdateTaskSensitiveRuleRequest,
)
from app.tasks.schemas.task_event import TaskEventResponse
from app.tasks.schemas.governed_route import RouteTaskRequest, RouteTaskResponse
from app.tasks.schemas.task_metrics import TaskGovernanceMetricsResponse
from app.tasks.deps.tasks import (
    get_task_service,
    get_task_queue_service,
    get_task_routing_rule_service,
    get_task_sensitive_rule_service,
    get_task_event_service,
    get_governed_task_center_service,
    get_task_metrics_service,
)
from app.tasks.services.task_service import TaskService
from app.tasks.services.task_queue_service import TaskQueueService
from app.tasks.services.task_routing_rule_service import TaskRoutingRuleService
from app.tasks.services.task_sensitive_rule_service import TaskSensitiveRuleService
from app.tasks.services.task_event_service import TaskEventService
from app.tasks.services.governed_task_center_service import GovernedTaskCenterService
from app.tasks.services.task_metrics_service import TaskMetricsService
from app.websocket.broadcasting_factory import get_broadcasting_service_dependency
from app.websocket.broadcasting_service import BroadcastingService
from app.tasks.services.task_intent_router_service import TaskIntentRouterService

logger = logging.getLogger(__name__)
router = APIRouter()


def _handle_unexpected_error(message: str, exc: Exception) -> SystemException:
    """封装系统异常，符合统一错误处理规范"""
    logger.error(f"{message}: {exc}", exc_info=True)
    return SystemException(message=message, code=ErrorCode.SYSTEM_ERROR)

def _require_admin(user: User) -> None:
    role = get_user_primary_role(user)
    if role not in {"admin", "admin", "super_admin"}:
        raise BusinessException(
            "仅管理员可操作",
            code=ErrorCode.PERMISSION_DENIED,
            status_code=status.HTTP_403_FORBIDDEN,
        )


@router.get("", response_model=ApiResponse[List[TaskResponse]])
async def get_tasks(
    status: Optional[str] = Query(None, description="状态筛选"),
    task_type: Optional[str] = Query(None, description="任务类型筛选"),
    priority: Optional[str] = Query(None, description="优先级筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    user_role: Optional[str] = Query(None, description="用户角色（用于筛选）"),
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
) -> ApiResponse[List[TaskResponse]]:
    """获取待办任务列表"""
    try:
        # 获取用户角色
        actual_user_role = user_role or get_user_primary_role(current_user)
        
        # 调用服务
        tasks = task_service.get_tasks_for_user(
            user_id=str(current_user.id),
            user_role=actual_user_role,
            status=status,
            task_type=task_type,
            priority=priority,
            search=search
        )
        
        return ApiResponse.success(tasks, message="获取任务列表成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("获取任务列表失败", e)


# =========================
# M1：可治理任务中枢（配置与路由）
# 注意：必须放在 /{task_id} 之前，避免被 path parameter 截获
# =========================

@router.get("/metrics", response_model=ApiResponse[TaskGovernanceMetricsResponse])
async def get_task_governance_metrics(
    start_at: Optional[datetime] = Query(None, description="起始时间（ISO，默认=近7天）"),
    end_at: Optional[datetime] = Query(None, description="结束时间（ISO，不含，默认=现在）"),
    scene_key: Optional[str] = Query(None, description="场景Key筛选（可选）"),
    current_user: User = Depends(get_current_user),
    service: TaskMetricsService = Depends(get_task_metrics_service),
) -> ApiResponse[TaskGovernanceMetricsResponse]:
    """M4：任务治理指标（用于数据统计看板）"""
    _require_admin(current_user)
    try:
        now = datetime.now(timezone.utc)
        end = end_at or now
        start = start_at or (end - timedelta(days=7))
        data = service.get_governance_metrics(start_at=start, end_at=end, scene_key=scene_key)
        return ApiResponse.success(data, message="获取任务治理指标成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("获取任务治理指标失败", e)


@router.get("/queues", response_model=ApiResponse[List[TaskQueueResponse]])
async def list_task_queues(
    scene_key: Optional[str] = Query(None, description="场景Key筛选"),
    only_active: bool = Query(False, description="仅返回启用队列"),
    current_user: User = Depends(get_current_user),
    service: TaskQueueService = Depends(get_task_queue_service),
) -> ApiResponse[List[TaskQueueResponse]]:
    _require_admin(current_user)
    data = service.list_queues(scene_key=scene_key, only_active=only_active)
    return ApiResponse.success(data, message="获取队列列表成功")


@router.post("/queues", response_model=ApiResponse[TaskQueueResponse], status_code=status.HTTP_201_CREATED)
async def create_task_queue(
    body: CreateTaskQueueRequest,
    current_user: User = Depends(get_current_user),
    service: TaskQueueService = Depends(get_task_queue_service),
) -> ApiResponse[TaskQueueResponse]:
    _require_admin(current_user)
    data = service.create_queue(body)
    return ApiResponse.success(data, message="创建队列成功")


@router.put("/queues/{queue_id}", response_model=ApiResponse[TaskQueueResponse])
async def update_task_queue(
    queue_id: str,
    body: UpdateTaskQueueRequest,
    current_user: User = Depends(get_current_user),
    service: TaskQueueService = Depends(get_task_queue_service),
) -> ApiResponse[TaskQueueResponse]:
    _require_admin(current_user)
    data = service.update_queue(queue_id, body)
    return ApiResponse.success(data, message="更新队列成功")


@router.delete("/queues/{queue_id}", response_model=ApiResponse[None])
async def delete_task_queue(
    queue_id: str,
    current_user: User = Depends(get_current_user),
    service: TaskQueueService = Depends(get_task_queue_service),
) -> ApiResponse[None]:
    _require_admin(current_user)
    service.delete_queue(queue_id)
    return ApiResponse.success(message="删除队列成功")


@router.get("/routing-rules", response_model=ApiResponse[List[TaskRoutingRuleResponse]])
async def list_task_routing_rules(
    scene_key: Optional[str] = Query(None, description="场景Key筛选"),
    enabled_only: bool = Query(False, description="仅启用规则"),
    current_user: User = Depends(get_current_user),
    service: TaskRoutingRuleService = Depends(get_task_routing_rule_service),
) -> ApiResponse[List[TaskRoutingRuleResponse]]:
    _require_admin(current_user)
    data = service.list_rules(scene_key=scene_key, enabled_only=enabled_only)
    return ApiResponse.success(data, message="获取路由规则成功")


@router.post("/routing-rules", response_model=ApiResponse[TaskRoutingRuleResponse], status_code=status.HTTP_201_CREATED)
async def create_task_routing_rule(
    body: CreateTaskRoutingRuleRequest,
    current_user: User = Depends(get_current_user),
    service: TaskRoutingRuleService = Depends(get_task_routing_rule_service),
) -> ApiResponse[TaskRoutingRuleResponse]:
    _require_admin(current_user)
    data = service.create_rule(body)
    return ApiResponse.success(data, message="创建路由规则成功")


@router.put("/routing-rules/{rule_id}", response_model=ApiResponse[TaskRoutingRuleResponse])
async def update_task_routing_rule(
    rule_id: str,
    body: UpdateTaskRoutingRuleRequest,
    current_user: User = Depends(get_current_user),
    service: TaskRoutingRuleService = Depends(get_task_routing_rule_service),
) -> ApiResponse[TaskRoutingRuleResponse]:
    _require_admin(current_user)
    data = service.update_rule(rule_id, body)
    return ApiResponse.success(data, message="更新路由规则成功")


@router.delete("/routing-rules/{rule_id}", response_model=ApiResponse[None])
async def delete_task_routing_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user),
    service: TaskRoutingRuleService = Depends(get_task_routing_rule_service),
) -> ApiResponse[None]:
    _require_admin(current_user)
    service.delete_rule(rule_id)
    return ApiResponse.success(message="删除路由规则成功")


@router.get("/sensitive-rules", response_model=ApiResponse[List[TaskSensitiveRuleResponse]])
async def list_task_sensitive_rules(
    category: Optional[str] = Query(None, description="分类筛选"),
    enabled_only: bool = Query(False, description="仅启用规则"),
    current_user: User = Depends(get_current_user),
    service: TaskSensitiveRuleService = Depends(get_task_sensitive_rule_service),
) -> ApiResponse[List[TaskSensitiveRuleResponse]]:
    _require_admin(current_user)
    data = service.list_rules(category=category, enabled_only=enabled_only)
    return ApiResponse.success(data, message="获取敏感规则成功")


@router.post("/sensitive-rules", response_model=ApiResponse[TaskSensitiveRuleResponse], status_code=status.HTTP_201_CREATED)
async def create_task_sensitive_rule(
    body: CreateTaskSensitiveRuleRequest,
    current_user: User = Depends(get_current_user),
    service: TaskSensitiveRuleService = Depends(get_task_sensitive_rule_service),
) -> ApiResponse[TaskSensitiveRuleResponse]:
    _require_admin(current_user)
    data = service.create_rule(body)
    return ApiResponse.success(data, message="创建敏感规则成功")


@router.put("/sensitive-rules/{rule_id}", response_model=ApiResponse[TaskSensitiveRuleResponse])
async def update_task_sensitive_rule(
    rule_id: str,
    body: UpdateTaskSensitiveRuleRequest,
    current_user: User = Depends(get_current_user),
    service: TaskSensitiveRuleService = Depends(get_task_sensitive_rule_service),
) -> ApiResponse[TaskSensitiveRuleResponse]:
    _require_admin(current_user)
    data = service.update_rule(rule_id, body)
    return ApiResponse.success(data, message="更新敏感规则成功")


@router.delete("/sensitive-rules/{rule_id}", response_model=ApiResponse[None])
async def delete_task_sensitive_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user),
    service: TaskSensitiveRuleService = Depends(get_task_sensitive_rule_service),
) -> ApiResponse[None]:
    _require_admin(current_user)
    service.delete_rule(rule_id)
    return ApiResponse.success(message="删除敏感规则成功")


@router.get("/events", response_model=ApiResponse[List[TaskEventResponse]])
async def list_task_events(
    task_id: str = Query(..., description="任务ID"),
    current_user: User = Depends(get_current_user),
    service: TaskEventService = Depends(get_task_event_service),
) -> ApiResponse[List[TaskEventResponse]]:
    _require_admin(current_user)
    data = service.list_events(task_id=task_id)
    return ApiResponse.success(data, message="获取任务事件成功")


@router.post("/route", response_model=ApiResponse[RouteTaskResponse], status_code=status.HTTP_201_CREATED)
async def route_task_and_create(
    body: RouteTaskRequest,
    current_user: User = Depends(get_current_user),
    service: GovernedTaskCenterService = Depends(get_governed_task_center_service),
    routing_rule_service: TaskRoutingRuleService = Depends(get_task_routing_rule_service),
    broadcasting_service: BroadcastingService = Depends(get_broadcasting_service_dependency),
) -> ApiResponse[RouteTaskResponse]:
    """M1：路由执行（场景+文本 → 敏感拦截 or 任务生成）"""
    # Copilot 模式：scene_key 可缺省，由 LLM 意图路由补全（失败则降级为关键词跨场景匹配）
    effective_body = body
    routed_intent: Optional[str] = None
    routed_confidence: Optional[float] = None
    if not (body.scene_key or "").strip():
        candidate_scenes = routing_rule_service.list_distinct_scene_keys()
        router_service = TaskIntentRouterService(db=service.db)
        scene_key, intent, confidence = await router_service.route_scene(
            text=body.text,
            user_id=str(current_user.id),
            candidate_scenes=candidate_scenes,
        )
        routed_intent = intent
        routed_confidence = confidence

        # 如果 LLM 未返回 scene_key，则降级：跨场景关键词匹配
        if not scene_key:
            hit = routing_rule_service.match_rule_any_scene(body.text.strip())
            scene_key = hit.scene_key if hit else None

        # 未识别到场景时：避免创建“需要配置”任务（Copilot 不打扰）
        if not scene_key:
            effective_body = body.model_copy(update={"create_fallback_task": False})
        else:
            effective_body = body.model_copy(update={"scene_key": scene_key, "create_fallback_task": False})

    data = service.route_and_create_tasks(user_id=str(current_user.id), request=effective_body)

    # 命中后主动提示（系统通知）
    try:
        if effective_body.conversation_id and data.route_type in {"routing", "sensitive"}:
            if data.route_type == "sensitive":
                title = "AI 副驾驶：风险提示"
                message = "监测到敏感表达风险，已给出安全改写建议"
                notify_type = "warning"
            else:
                title = "AI 副驾驶：建议处理"
                message = f"监测到业务意图，已生成 {len(data.created_tasks)} 条任务草稿"
                notify_type = "info"

            await broadcasting_service.broadcast_system_notification(
                conversation_id=effective_body.conversation_id,
                notification_data={
                    "title": title,
                    "message": message,
                    "type": notify_type,
                    "extra": {
                        "route_type": data.route_type,
                        "matched_rule_id": data.matched_rule_id,
                        "matched_sensitive_rule_id": data.matched_sensitive_rule_id,
                        "intent": routed_intent,
                        "confidence": routed_confidence,
                        "task_ids": [t.id for t in data.created_tasks],
                    },
                },
            )
    except Exception as e:
        logger.warning(f"路由系统通知广播失败（已忽略）: {e}", exc_info=True)

    return ApiResponse.success(data, message="路由执行成功")


@router.get("/{task_id}", response_model=ApiResponse[TaskResponse])
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
) -> ApiResponse[TaskResponse]:
    """获取任务详情"""
    try:
        user_role = get_user_primary_role(current_user)
        
        # 调用服务
        task = task_service.get_task_by_id(
            task_id=task_id,
            user_id=str(current_user.id),
            user_role=user_role
        )
        
        if not task:
            raise BusinessException(
                "任务不存在或无权限访问",
                code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND,
            )
        
        return ApiResponse.success(task, message="获取任务详情成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("获取任务详情失败", e)


@router.post("", response_model=ApiResponse[TaskResponse], status_code=status.HTTP_201_CREATED)
async def create_task(
    data: CreateTaskRequest,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
) -> ApiResponse[TaskResponse]:
    """创建待办任务"""
    try:
        # 调用服务
        task = task_service.create_task(
            user_id=str(current_user.id),
            task_data=data
        )
        
        return ApiResponse.success(task, message="创建任务成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("创建任务失败", e)


@router.post("/{task_id}/claim", response_model=ApiResponse[TaskResponse])
async def claim_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
) -> ApiResponse[TaskResponse]:
    """认领任务"""
    try:
        # 调用服务
        task = task_service.claim_task(
            task_id=task_id,
            user_id=str(current_user.id)
        )
        
        return ApiResponse.success(task, message="认领任务成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("认领任务失败", e)


@router.put("/{task_id}", response_model=ApiResponse[TaskResponse])
async def update_task(
    task_id: str,
    data: UpdateTaskRequest,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
) -> ApiResponse[TaskResponse]:
    """更新任务状态"""
    try:
        user_role = get_user_primary_role(current_user)
        
        # 调用服务
        task = task_service.update_task(
            task_id=task_id,
            user_id=str(current_user.id),
            user_role=user_role,
            task_data=data
        )
        
        return ApiResponse.success(task, message="更新任务成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("更新任务失败", e)
