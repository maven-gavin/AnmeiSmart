from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
import enum


class PlanStatusEnum(str, enum.Enum):
    """方案状态枚举"""
    DRAFT = "DRAFT"
    SHARED = "SHARED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class RiskToleranceEnum(str, enum.Enum):
    """风险承受度枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# 基础Schema类
class BaseConsultantSchema(BaseModel):
    class Config:
        from_attributes = True


# 个性化方案相关Schema
class CustomerProfile(BaseConsultantSchema):
    """客户画像Schema"""
    age: Optional[int] = None
    gender: Optional[str] = None  # male, female
    concerns: List[str] = []
    budget: Optional[float] = None
    expected_results: Optional[str] = None


class ProjectDetail(BaseConsultantSchema):
    """项目详情Schema"""
    id: str
    name: str
    description: str
    cost: float
    duration: str
    recovery_time: str
    expected_results: str
    risks: List[str] = []


class PersonalizedPlanResponse(BaseConsultantSchema):
    """个性化方案响应Schema"""
    id: str
    customer_id: str
    customer_name: str
    consultant_id: str
    consultant_name: str
    customer_profile: Optional[CustomerProfile] = None
    projects: List[ProjectDetail] = []
    total_cost: float = 0.0
    estimated_timeframe: Optional[str] = None
    status: PlanStatusEnum = PlanStatusEnum.DRAFT
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    @staticmethod
    def from_model(plan) -> "PersonalizedPlanResponse":
        """将ORM模型转换为Schema"""
        # 转换customer_profile JSON
        customer_profile = None
        if plan.customer_profile:
            customer_profile = CustomerProfile(**plan.customer_profile)
        
        # 转换projects JSON为ProjectDetail列表
        projects = []
        if plan.projects:
            for project_data in plan.projects:
                projects.append(ProjectDetail(**project_data))
        
        return PersonalizedPlanResponse(
            id=plan.id,
            customer_id=plan.customer_id,
            customer_name=plan.customer_name,
            consultant_id=plan.consultant_id,
            consultant_name=plan.consultant_name,
            customer_profile=customer_profile,
            projects=projects,
            total_cost=plan.total_cost,
            estimated_timeframe=plan.estimated_timeframe,
            status=plan.status,
            notes=plan.notes,
            created_at=plan.created_at,
            updated_at=plan.updated_at
        )


class PersonalizedPlanCreate(BaseConsultantSchema):
    """创建个性化方案Schema"""
    customer_id: str
    customer_name: str = Field(..., max_length=100)
    customer_profile: Optional[CustomerProfile] = None
    projects: List[ProjectDetail] = []
    estimated_timeframe: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class PersonalizedPlanUpdate(BaseConsultantSchema):
    """更新个性化方案Schema"""
    customer_profile: Optional[CustomerProfile] = None
    projects: Optional[List[ProjectDetail]] = None
    estimated_timeframe: Optional[str] = Field(None, max_length=100)
    status: Optional[PlanStatusEnum] = None
    notes: Optional[str] = None


# 术前模拟相关Schema
class SimulationImageResponse(BaseConsultantSchema):
    """术前模拟图像响应Schema"""
    id: str
    customer_id: str
    customer_name: str
    original_image_path: str
    simulated_image_path: str
    project_type_id: str
    parameters: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    consultant_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    @staticmethod
    def from_model(simulation_image) -> "SimulationImageResponse":
        """将ORM模型转换为Schema"""
        return SimulationImageResponse(
            id=simulation_image.id,
            customer_id=simulation_image.customer_id,
            customer_name=simulation_image.customer_name,
            original_image_path=simulation_image.original_image_path,
            simulated_image_path=simulation_image.simulated_image_path,
            project_type_id=simulation_image.project_type_id,
            parameters=simulation_image.parameters,
            notes=simulation_image.notes,
            consultant_id=simulation_image.consultant_id,
            created_at=simulation_image.created_at,
            updated_at=simulation_image.updated_at
        )


class SimulationImageCreate(BaseConsultantSchema):
    """创建术前模拟Schema"""
    customer_id: str
    customer_name: str = Field(..., max_length=100)
    project_type_id: str
    parameters: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


# 项目类型相关Schema
class SimulationParameter(BaseConsultantSchema):
    """模拟参数Schema"""
    id: str
    name: str
    label: str
    type: str  # slider, select, radio
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    options: Optional[List[Dict[str, str]]] = None
    default_value: Union[str, float]


class ProjectTypeResponse(BaseConsultantSchema):
    """项目类型响应Schema"""
    id: str
    name: str
    label: str
    description: Optional[str] = None
    parameters: Optional[List[SimulationParameter]] = None
    is_active: bool = True
    category: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    @staticmethod
    def from_model(project_type) -> "ProjectTypeResponse":
        """将ORM模型转换为Schema"""
        # 转换parameters JSON为SimulationParameter列表
        parameters = []
        if project_type.parameters:
            for param_data in project_type.parameters:
                parameters.append(SimulationParameter(**param_data))
        
        return ProjectTypeResponse(
            id=project_type.id,
            name=project_type.name,
            label=project_type.label,
            description=project_type.description,
            parameters=parameters,
            is_active=project_type.is_active,
            category=project_type.category,
            created_at=project_type.created_at,
            updated_at=project_type.updated_at
        )


# 项目模板相关Schema
class ProjectTemplateResponse(BaseConsultantSchema):
    """项目模板响应Schema"""
    id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    base_cost: float
    duration: Optional[str] = None
    recovery_time: Optional[str] = None
    expected_results: Optional[str] = None
    risks: List[str] = []
    is_active: bool = True
    suitable_age_min: Optional[int] = None
    suitable_age_max: Optional[int] = None
    suitable_concerns: List[str] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    @staticmethod
    def from_model(template) -> "ProjectTemplateResponse":
        """将ORM模型转换为Schema"""
        return ProjectTemplateResponse(
            id=template.id,
            name=template.name,
            description=template.description,
            category=template.category,
            base_cost=template.base_cost,
            duration=template.duration,
            recovery_time=template.recovery_time,
            expected_results=template.expected_results,
            risks=template.risks or [],
            is_active=template.is_active,
            suitable_age_min=template.suitable_age_min,
            suitable_age_max=template.suitable_age_max,
            suitable_concerns=template.suitable_concerns or [],
            created_at=template.created_at,
            updated_at=template.updated_at
        )


# 客户偏好相关Schema
class CustomerPreferenceResponse(BaseConsultantSchema):
    """客户偏好响应Schema"""
    id: str
    customer_id: str
    preferred_budget_min: Optional[float] = None
    preferred_budget_max: Optional[float] = None
    preferred_recovery_time: Optional[str] = None
    preferred_project_categories: List[str] = []
    concerns_history: List[str] = []
    risk_tolerance: RiskToleranceEnum = RiskToleranceEnum.MEDIUM
    created_at: datetime
    updated_at: Optional[datetime] = None

    @staticmethod
    def from_model(preference) -> "CustomerPreferenceResponse":
        """将ORM模型转换为Schema"""
        return CustomerPreferenceResponse(
            id=preference.id,
            customer_id=preference.customer_id,
            preferred_budget_min=preference.preferred_budget_min,
            preferred_budget_max=preference.preferred_budget_max,
            preferred_recovery_time=preference.preferred_recovery_time,
            preferred_project_categories=preference.preferred_project_categories or [],
            concerns_history=preference.concerns_history or [],
            risk_tolerance=preference.risk_tolerance,
            created_at=preference.created_at,
            updated_at=preference.updated_at
        )


class CustomerPreferenceUpdate(BaseConsultantSchema):
    """更新客户偏好Schema"""
    preferred_budget_min: Optional[float] = Field(None, ge=0)
    preferred_budget_max: Optional[float] = Field(None, ge=0)
    preferred_recovery_time: Optional[str] = Field(None, max_length=50)
    preferred_project_categories: Optional[List[str]] = None
    concerns_history: Optional[List[str]] = None
    risk_tolerance: Optional[RiskToleranceEnum] = None


# 方案推荐相关Schema
class RecommendationRequest(BaseConsultantSchema):
    """方案推荐请求Schema"""
    customer_id: str
    customer_profile: CustomerProfile
    preferences: Optional[Dict[str, Any]] = None


class RecommendationResponse(BaseConsultantSchema):
    """方案推荐响应Schema"""
    recommended_projects: List[ProjectTemplateResponse]
    total_estimated_cost: float
    confidence_score: float = Field(..., ge=0, le=1)
    reasoning: str