from sqlalchemy import Column, String, Text, Boolean, Integer, Enum, JSON, Index

from app.common.models.base_model import BaseModel


class TaskRoutingRule(BaseModel):
    """任务路由规则（M0占位）- 场景+关键词 → 动作模板/目标Agent 的映射"""

    __tablename__ = "task_routing_rules"
    __table_args__ = (
        Index("idx_task_routing_rule_scene_key", "scene_key"),
        Index("idx_task_routing_rule_enabled", "enabled"),
        {"comment": "任务路由规则表（M0占位），用于关键词触发路由到Agent/模板"},
    )

    scene_key = Column(String(100), nullable=False, comment="场景Key，如 sales_delivery")
    keyword = Column(String(200), nullable=False, comment="关键词/短语（M0：简单包含匹配）")
    match_type = Column(
        Enum("contains", "regex", name="task_routing_rule_match_type"),
        nullable=False,
        default="contains",
        comment="匹配类型",
    )
    priority = Column(Integer, nullable=False, default=100, comment="规则优先级（越小越优先）")

    target = Column(String(200), nullable=True, comment="目标（Agent/Workflow标识，M0占位）")
    task_templates = Column(JSON, nullable=True, comment="命中后要生成的任务模板（JSON）")
    description = Column(Text, nullable=True, comment="规则说明")

    enabled = Column(Boolean, nullable=False, default=True, comment="是否启用")


