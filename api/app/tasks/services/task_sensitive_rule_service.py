import re
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.api import BusinessException, ErrorCode
from app.tasks.models import TaskSensitiveRule
from app.tasks.schemas.sensitive_rule import (
    CreateTaskSensitiveRuleRequest,
    TaskSensitiveRuleResponse,
    UpdateTaskSensitiveRuleRequest,
)


class TaskSensitiveRuleService:
    """敏感规则服务（M1）"""

    def __init__(self, db: Session):
        self.db = db

    def list_rules(self, category: Optional[str] = None, enabled_only: bool = False) -> List[TaskSensitiveRuleResponse]:
        query = self.db.query(TaskSensitiveRule)
        if category:
            query = query.filter(TaskSensitiveRule.category == category)
        if enabled_only:
            query = query.filter(TaskSensitiveRule.enabled.is_(True))
        rules = query.order_by(TaskSensitiveRule.priority.asc(), TaskSensitiveRule.created_at.desc()).all()
        return [
            TaskSensitiveRuleResponse(
                id=r.id,
                category=r.category,
                pattern=r.pattern,
                match_type=r.match_type,
                priority=r.priority,
                suggestion_templates=r.suggestion_templates,
                description=r.description,
                enabled=r.enabled,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in rules
        ]

    def get_by_id(self, rule_id: str) -> TaskSensitiveRule:
        rule = self.db.query(TaskSensitiveRule).filter(TaskSensitiveRule.id == rule_id).first()
        if not rule:
            raise BusinessException("敏感规则不存在", code=ErrorCode.NOT_FOUND)
        return rule

    def create_rule(self, data: CreateTaskSensitiveRuleRequest) -> TaskSensitiveRuleResponse:
        rule = TaskSensitiveRule(
            category=data.category,
            pattern=data.pattern,
            match_type=data.match_type,
            priority=data.priority,
            suggestion_templates=data.suggestion_templates,
            description=data.description,
            enabled=data.enabled,
        )
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return TaskSensitiveRuleResponse(
            id=rule.id,
            category=rule.category,
            pattern=rule.pattern,
            match_type=rule.match_type,
            priority=rule.priority,
            suggestion_templates=rule.suggestion_templates,
            description=rule.description,
            enabled=rule.enabled,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
        )

    def update_rule(self, rule_id: str, data: UpdateTaskSensitiveRuleRequest) -> TaskSensitiveRuleResponse:
        rule = self.get_by_id(rule_id)
        if data.category is not None:
            rule.category = data.category
        if data.pattern is not None:
            rule.pattern = data.pattern
        if data.match_type is not None:
            rule.match_type = data.match_type
        if data.priority is not None:
            rule.priority = data.priority
        if data.suggestion_templates is not None:
            rule.suggestion_templates = data.suggestion_templates
        if data.description is not None:
            rule.description = data.description
        if data.enabled is not None:
            rule.enabled = data.enabled

        self.db.commit()
        self.db.refresh(rule)
        return TaskSensitiveRuleResponse(
            id=rule.id,
            category=rule.category,
            pattern=rule.pattern,
            match_type=rule.match_type,
            priority=rule.priority,
            suggestion_templates=rule.suggestion_templates,
            description=rule.description,
            enabled=rule.enabled,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
        )

    def delete_rule(self, rule_id: str) -> None:
        rule = self.get_by_id(rule_id)
        self.db.delete(rule)
        self.db.commit()

    def detect(self, text: str) -> Optional[Tuple[TaskSensitiveRule, str]]:
        """返回命中的第一条敏感规则 + 分类字符串"""
        rules = (
            self.db.query(TaskSensitiveRule)
            .filter(TaskSensitiveRule.enabled.is_(True))
            .order_by(TaskSensitiveRule.priority.asc(), TaskSensitiveRule.created_at.desc())
            .all()
        )
        for r in rules:
            if r.match_type == "regex":
                try:
                    if re.search(r.pattern, text):
                        return r, str(r.category)
                except re.error:
                    continue
            else:
                if r.pattern in text:
                    return r, str(r.category)
        return None


