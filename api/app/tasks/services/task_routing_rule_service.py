import re
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.api import BusinessException, ErrorCode
from app.tasks.models import TaskRoutingRule
from app.tasks.schemas.routing_rule import (
    CreateTaskRoutingRuleRequest,
    TaskRoutingRuleResponse,
    UpdateTaskRoutingRuleRequest,
)


class TaskRoutingRuleService:
    """任务路由规则服务（M1）"""

    def __init__(self, db: Session):
        self.db = db

    def list_rules(self, scene_key: Optional[str] = None, enabled_only: bool = False) -> List[TaskRoutingRuleResponse]:
        query = self.db.query(TaskRoutingRule)
        if scene_key:
            query = query.filter(TaskRoutingRule.scene_key == scene_key)
        if enabled_only:
            query = query.filter(TaskRoutingRule.enabled.is_(True))
        rules = query.order_by(TaskRoutingRule.priority.asc(), TaskRoutingRule.created_at.desc()).all()
        return [
            TaskRoutingRuleResponse(
                id=r.id,
                scene_key=r.scene_key,
                keyword=r.keyword,
                match_type=r.match_type,
                priority=r.priority,
                target=r.target,
                task_templates=r.task_templates,
                description=r.description,
                enabled=r.enabled,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in rules
        ]

    def get_by_id(self, rule_id: str) -> TaskRoutingRule:
        rule = self.db.query(TaskRoutingRule).filter(TaskRoutingRule.id == rule_id).first()
        if not rule:
            raise BusinessException("路由规则不存在", code=ErrorCode.NOT_FOUND)
        return rule

    def create_rule(self, data: CreateTaskRoutingRuleRequest) -> TaskRoutingRuleResponse:
        rule = TaskRoutingRule(
            scene_key=data.scene_key,
            keyword=data.keyword,
            match_type=data.match_type,
            priority=data.priority,
            target=data.target,
            task_templates=data.task_templates,
            description=data.description,
            enabled=data.enabled,
        )
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return TaskRoutingRuleResponse(
            id=rule.id,
            scene_key=rule.scene_key,
            keyword=rule.keyword,
            match_type=rule.match_type,
            priority=rule.priority,
            target=rule.target,
            task_templates=rule.task_templates,
            description=rule.description,
            enabled=rule.enabled,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
        )

    def update_rule(self, rule_id: str, data: UpdateTaskRoutingRuleRequest) -> TaskRoutingRuleResponse:
        rule = self.get_by_id(rule_id)
        if data.scene_key is not None:
            rule.scene_key = data.scene_key
        if data.keyword is not None:
            rule.keyword = data.keyword
        if data.match_type is not None:
            rule.match_type = data.match_type
        if data.priority is not None:
            rule.priority = data.priority
        if data.target is not None:
            rule.target = data.target
        if data.task_templates is not None:
            rule.task_templates = data.task_templates
        if data.description is not None:
            rule.description = data.description
        if data.enabled is not None:
            rule.enabled = data.enabled

        self.db.commit()
        self.db.refresh(rule)
        return TaskRoutingRuleResponse(
            id=rule.id,
            scene_key=rule.scene_key,
            keyword=rule.keyword,
            match_type=rule.match_type,
            priority=rule.priority,
            target=rule.target,
            task_templates=rule.task_templates,
            description=rule.description,
            enabled=rule.enabled,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
        )

    def delete_rule(self, rule_id: str) -> None:
        rule = self.get_by_id(rule_id)
        self.db.delete(rule)
        self.db.commit()

    def match_rule(self, scene_key: str, text: str) -> Optional[TaskRoutingRule]:
        """根据 scene_key + text 返回命中的第一个规则（按 priority 升序）"""
        rules = (
            self.db.query(TaskRoutingRule)
            .filter(TaskRoutingRule.scene_key == scene_key, TaskRoutingRule.enabled.is_(True))
            .order_by(TaskRoutingRule.priority.asc(), TaskRoutingRule.created_at.desc())
            .all()
        )
        for r in rules:
            if r.match_type == "regex":
                try:
                    if re.search(r.keyword, text):
                        return r
                except re.error:
                    # 无效正则忽略（M1 不强校验，避免阻塞）
                    continue
            else:
                if r.keyword in text:
                    return r
        return None

    def list_distinct_scene_keys(self) -> List[str]:
        rows = (
            self.db.query(TaskRoutingRule.scene_key)
            .filter(TaskRoutingRule.enabled.is_(True))
            .distinct()
            .order_by(TaskRoutingRule.scene_key.asc())
            .all()
        )
        return [r[0] for r in rows if r and r[0]]

    def match_rule_any_scene(self, text: str) -> Optional[TaskRoutingRule]:
        """不指定 scene_key：在所有启用规则里匹配，返回命中的第一个（按 priority 升序）"""
        rules = (
            self.db.query(TaskRoutingRule)
            .filter(TaskRoutingRule.enabled.is_(True))
            .order_by(TaskRoutingRule.priority.asc(), TaskRoutingRule.created_at.desc())
            .all()
        )
        for r in rules:
            if r.match_type == "regex":
                try:
                    if re.search(r.keyword, text):
                        return r
                except re.error:
                    continue
            else:
                if r.keyword in text:
                    return r
        return None


