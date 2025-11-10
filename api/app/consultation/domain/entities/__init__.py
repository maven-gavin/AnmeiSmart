"""
实体层
定义咨询领域中的聚合根和实体
"""
from .consultation import ConsultationEntity
from .plan import PlanEntity
from .consultant import ConsultantEntity

__all__ = [
    "ConsultationEntity",
    "PlanEntity",
    "ConsultantEntity"
]
