from sqlalchemy import Column, String, Text, Boolean, Integer, Enum, JSON, Index

from app.common.models.base_model import BaseModel


class TaskSensitiveRule(BaseModel):
    """敏感规则（M0占位）- 用于 D2 敏感拦截与安全改写建议"""

    __tablename__ = "task_sensitive_rules"
    __table_args__ = (
        Index("idx_task_sensitive_rule_category", "category"),
        Index("idx_task_sensitive_rule_enabled", "enabled"),
        {"comment": "任务敏感规则表（M0占位），用于少数风险拦截与建议生成"},
    )

    category = Column(
        Enum("pricing", "commitment", "confidential", "destructive", name="task_sensitive_category"),
        nullable=False,
        comment="敏感分类",
    )
    pattern = Column(String(300), nullable=False, comment="规则匹配模式（M0：简单包含/可扩展regex）")
    match_type = Column(
        Enum("contains", "regex", name="task_sensitive_rule_match_type"),
        nullable=False,
        default="contains",
        comment="匹配类型",
    )
    priority = Column(Integer, nullable=False, default=100, comment="规则优先级（越小越优先）")

    suggestion_templates = Column(JSON, nullable=True, comment="安全改写建议模板（JSON）")
    description = Column(Text, nullable=True, comment="规则说明")

    enabled = Column(Boolean, nullable=False, default=True, comment="是否启用")


