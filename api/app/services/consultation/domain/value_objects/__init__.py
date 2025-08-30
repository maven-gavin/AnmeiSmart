"""
值对象层
定义咨询领域中的值对象
"""
from .consultation_status import ConsultationStatus
from .plan_status import PlanStatus

__all__ = [
    "ConsultationStatus",
    "PlanStatus"
]
