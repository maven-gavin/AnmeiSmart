"""
咨询模块数据库模型导出

导出该领域的所有数据库模型，确保SQLAlchemy可以正确建立关系映射。
"""

from .plan_generation import PlanGenerationSession, PlanDraft, InfoCompleteness
from .consultant import ProjectTemplate, ProjectType, PersonalizedPlan, PlanStatusEnum, SimulationImage, PlanVersion

__all__ = [
    "PlanGenerationSession", "PlanDraft", "InfoCompleteness",
    "ProjectTemplate", "ProjectType", "PersonalizedPlan", "PlanStatusEnum", 
    "SimulationImage", "PlanVersion"
]
