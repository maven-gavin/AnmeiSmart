"""
咨询领域层
包含领域实体、值对象、领域服务和领域事件
"""
from .entities.consultation import Consultation
from .entities.plan import Plan
from .entities.consultant import Consultant
from .value_objects.consultation_status import ConsultationStatus
from .value_objects.plan_status import PlanStatus
from .consultation_domain_service import ConsultationDomainService
from .plan_generation_domain_service import PlanGenerationDomainService
from .consultant_domain_service import ConsultantDomainService

__all__ = [
    "Consultation",
    "Plan", 
    "Consultant",
    "ConsultationStatus",
    "PlanStatus",
    "ConsultationDomainService",
    "PlanGenerationDomainService",
    "ConsultantDomainService"
]
