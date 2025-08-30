"""
咨询领域Schema定义
包含咨询、顾问、方案生成、项目类型、客户偏好等相关的数据模型
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal, Union
from pydantic import BaseModel, ConfigDict, Field
from enum import Enum


# ===== 枚举类型定义 =====

class PlanStatusEnum(str, Enum):
    """方案状态枚举"""
    DRAFT = "DRAFT"
    SHARED = "SHARED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class RiskToleranceEnum(str, Enum):
    """风险承受度枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PlanSessionStatus(str, Enum):
    """方案生成会话状态枚举"""
    collecting = "collecting"    # 收集中
    generating = "generating"    # 生成中
    optimizing = "optimizing"    # 优化中
    reviewing = "reviewing"      # 审核中
    completed = "completed"      # 已完成
    failed = "failed"           # 失败
    cancelled = "cancelled"     # 已取消


class PlanDraftStatus(str, Enum):
    """方案草稿状态枚举"""
    draft = "draft"             # 草稿
    reviewing = "reviewing"     # 审核中
    approved = "approved"       # 已确认
    rejected = "rejected"       # 已拒绝
    archived = "archived"       # 已归档


class InfoStatus(str, Enum):
    """信息完整性状态枚举"""
    missing = "missing"         # 缺失
    partial = "partial"         # 部分
    complete = "complete"       # 完整


# ===== 基础Schema类 =====

class BaseConsultantSchema(BaseModel):
    """基础Schema类"""
    class Config:
        from_attributes = True


# ===== 值对象Schema =====

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


# ===== AI辅助方案生成信息结构 =====

class BasicInfo(BaseModel):
    """基础信息结构"""
    age: Optional[int] = None
    gender: Optional[str] = None
    skin_type: Optional[str] = None
    medical_history: Optional[List[str]] = None


class ConcernsInfo(BaseModel):
    """关注点信息结构"""
    primary_concern: Optional[str] = None
    secondary_concerns: Optional[List[str]] = None
    severity_level: Optional[str] = None
    affected_areas: Optional[List[str]] = None


class BudgetInfo(BaseModel):
    """预算信息结构"""
    budget_range: Optional[str] = None
    payment_preference: Optional[str] = None
    flexibility: Optional[str] = None


class TimelineInfo(BaseModel):
    """时间安排信息结构"""
    preferred_start_date: Optional[str] = None
    availability: Optional[str] = None
    urgency_level: Optional[str] = None


class ExpectationsInfo(BaseModel):
    """期望信息结构"""
    desired_outcome: Optional[str] = None
    previous_experience: Optional[str] = None
    risk_tolerance: Optional[str] = None


class ExtractedInfo(BaseModel):
    """提取的客户信息结构"""
    basic_info: Optional[BasicInfo] = None
    concerns: Optional[ConcernsInfo] = None
    budget: Optional[BudgetInfo] = None
    timeline: Optional[TimelineInfo] = None
    expectations: Optional[ExpectationsInfo] = None
    additional_notes: Optional[str] = None
    extraction_confidence: Optional[float] = None
    last_updated: Optional[str] = None


# ===== 方案内容结构 =====

class PlanBasicInfo(BaseModel):
    """方案基础信息"""
    title: str = Field(..., description="方案标题")
    description: str = Field(..., description="方案描述")
    target_concerns: List[str] = Field(default=[], description="目标关注点")
    difficulty_level: Optional[str] = Field(None, description="难度级别")
    total_duration: Optional[str] = Field(None, description="总时长")


class PlanAnalysis(BaseModel):
    """方案分析"""
    skin_analysis: Optional[str] = Field(None, description="皮肤状态分析")
    concern_priority: List[str] = Field(default=[], description="关注点优先级")
    treatment_approach: Optional[str] = Field(None, description="治疗方法")
    expected_timeline: Optional[str] = Field(None, description="预期时间线")


class TreatmentItem(BaseModel):
    """治疗项目"""
    name: str = Field(..., description="治疗名称")
    frequency: Optional[str] = Field(None, description="频率")
    sessions: Optional[int] = Field(None, description="疗程次数")
    price_per_session: Optional[float] = Field(None, description="单次价格")
    total_price: Optional[float] = Field(None, description="总价")


class TreatmentPhase(BaseModel):
    """治疗阶段"""
    phase: int = Field(..., description="阶段序号")
    name: str = Field(..., description="阶段名称")
    duration: Optional[str] = Field(None, description="持续时间")
    treatments: List[TreatmentItem] = Field(default=[], description="治疗项目")


class TreatmentPlan(BaseModel):
    """治疗计划"""
    phases: List[TreatmentPhase] = Field(default=[], description="治疗阶段")


class CostBreakdown(BaseModel):
    """费用明细"""
    treatment_costs: Optional[float] = Field(None, description="治疗费用")
    product_costs: Optional[float] = Field(None, description="产品费用")
    maintenance_costs: Optional[float] = Field(None, description="维护费用")
    total_cost: Optional[float] = Field(None, description="总费用")
    payment_options: List[str] = Field(default=[], description="付款方式")


class Milestone(BaseModel):
    """时间节点"""
    date: str = Field(..., description="日期")
    milestone: str = Field(..., description="里程碑")


class PlanTimeline(BaseModel):
    """方案时间线"""
    start_date: Optional[str] = Field(None, description="开始日期")
    key_milestones: List[Milestone] = Field(default=[], description="关键节点")
    completion_date: Optional[str] = Field(None, description="完成日期")


class RisksAndPrecautions(BaseModel):
    """风险和注意事项"""
    potential_risks: List[str] = Field(default=[], description="潜在风险")
    contraindications: List[str] = Field(default=[], description="禁忌症")
    precautions: List[str] = Field(default=[], description="注意事项")
    emergency_contact: Optional[str] = Field(None, description="紧急联系方式")


class Aftercare(BaseModel):
    """后续护理"""
    immediate_care: List[str] = Field(default=[], description="即时护理")
    long_term_care: List[str] = Field(default=[], description="长期护理")
    product_recommendations: List[str] = Field(default=[], description="产品推荐")


class PlanContent(BaseModel):
    """方案内容结构"""
    basic_info: PlanBasicInfo = Field(..., description="基础信息")
    analysis: Optional[PlanAnalysis] = Field(None, description="分析")
    treatment_plan: Optional[TreatmentPlan] = Field(None, description="治疗计划")
    cost_breakdown: Optional[CostBreakdown] = Field(None, description="费用明细")
    timeline: Optional[PlanTimeline] = Field(None, description="时间线")
    risks_and_precautions: Optional[RisksAndPrecautions] = Field(None, description="风险和注意事项")
    aftercare: Optional[Aftercare] = Field(None, description="后续护理")


# ===== 反馈结构 =====

class ConsultantFeedback(BaseModel):
    """顾问反馈"""
    rating: Optional[int] = Field(None, ge=1, le=5, description="评分")
    comments: Optional[str] = Field(None, description="评论")
    suggestions: List[str] = Field(default=[], description="建议")
    timestamp: Optional[str] = Field(None, description="时间戳")
    consultant_id: Optional[str] = Field(None, description="顾问ID")


class CustomerFeedback(BaseModel):
    """客户反馈"""
    rating: Optional[int] = Field(None, ge=1, le=5, description="评分")
    comments: Optional[str] = Field(None, description="评论")
    concerns: List[str] = Field(default=[], description="关注点")
    preferences: List[str] = Field(default=[], description="偏好")
    timestamp: Optional[str] = Field(None, description="时间戳")
    customer_id: Optional[str] = Field(None, description="客户ID")


class MedicalReview(BaseModel):
    """医学审核"""
    approved: Optional[bool] = Field(None, description="是否批准")
    reviewer: Optional[str] = Field(None, description="审核人")
    comments: Optional[str] = Field(None, description="审核意见")
    modifications: List[str] = Field(default=[], description="修改建议")
    timestamp: Optional[str] = Field(None, description="时间戳")


class PlanFeedback(BaseModel):
    """方案反馈"""
    consultant_feedback: Optional[ConsultantFeedback] = None
    customer_feedback: Optional[CustomerFeedback] = None
    medical_review: Optional[MedicalReview] = None


# ===== 引导问题结构 =====

class GuidanceQuestion(BaseModel):
    """引导问题"""
    field: str = Field(..., description="字段名")
    question: str = Field(..., description="问题内容")
    priority: Literal["high", "medium", "low"] = Field(..., description="优先级")
    category: str = Field(..., description="类别")


class GuidanceQuestions(BaseModel):
    """引导问题集合"""
    basic_info: List[GuidanceQuestion] = Field(default=[], description="基础信息问题")
    concerns: List[GuidanceQuestion] = Field(default=[], description="关注点问题")
    budget: List[GuidanceQuestion] = Field(default=[], description="预算问题")
    timeline: List[GuidanceQuestion] = Field(default=[], description="时间安排问题")
    expectations: List[GuidanceQuestion] = Field(default=[], description="期望问题")
    generated_at: Optional[str] = Field(None, description="生成时间")
    total_questions: Optional[int] = Field(None, description="总问题数")


# ===== 基础咨询Schema =====

class ConsultationCreate(BaseModel):
    """创建咨询请求"""
    customer_id: str = Field(..., description="客户ID")
    title: str = Field(..., description="咨询标题")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class ConsultationUpdate(BaseModel):
    """更新咨询请求"""
    title: Optional[str] = Field(default=None, description="咨询标题")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class ConsultationResponse(BaseModel):
    """咨询响应"""
    id: str = Field(..., description="咨询ID")
    customer_id: str = Field(..., description="客户ID")
    consultant_id: Optional[str] = Field(default=None, description="顾问ID")
    status: str = Field(..., description="咨询状态")
    title: str = Field(..., description="咨询标题")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class ConsultationListResponse(BaseModel):
    """咨询列表响应"""
    consultations: List[ConsultationResponse] = Field(..., description="咨询列表")
    total: int = Field(..., description="总数")


# ===== 顾问管理Schema =====

class ConsultantCreate(BaseModel):
    """创建顾问请求"""
    user_id: str = Field(..., description="用户ID")
    name: str = Field(..., description="顾问姓名")
    specialization: str = Field(..., description="专业领域")
    experience_years: int = Field(..., description="工作经验年数")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class ConsultantUpdate(BaseModel):
    """更新顾问请求"""
    name: Optional[str] = Field(default=None, description="顾问姓名")
    specialization: Optional[str] = Field(default=None, description="专业领域")
    experience_years: Optional[int] = Field(default=None, description="工作经验年数")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class ConsultantResponse(BaseModel):
    """顾问响应"""
    id: str = Field(..., description="顾问ID")
    user_id: str = Field(..., description="用户ID")
    name: str = Field(..., description="顾问姓名")
    specialization: str = Field(..., description="专业领域")
    experience_years: int = Field(..., description="工作经验年数")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class ConsultantListResponse(BaseModel):
    """顾问列表响应"""
    consultants: List[ConsultantResponse] = Field(..., description="顾问列表")
    total: int = Field(..., description="总数")


# ===== 项目类型和模板Schema =====

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


# ===== 客户偏好Schema =====

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


class CustomerPreferenceUpdate(BaseConsultantSchema):
    """更新客户偏好Schema"""
    preferred_budget_min: Optional[float] = Field(None, ge=0)
    preferred_budget_max: Optional[float] = Field(None, ge=0)
    preferred_recovery_time: Optional[str] = Field(None, max_length=50)
    preferred_project_categories: Optional[List[str]] = None
    concerns_history: Optional[List[str]] = None
    risk_tolerance: Optional[RiskToleranceEnum] = None


# ===== 术前模拟Schema =====

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


class SimulationImageCreate(BaseConsultantSchema):
    """创建术前模拟Schema"""
    customer_id: str
    customer_name: str = Field(..., max_length=100)
    project_type_id: str
    parameters: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


# ===== 个性化方案Schema =====

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


# ===== 方案推荐Schema =====

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


# ===== AI辅助方案生成Schema =====

class PlanGenerationSessionBase(BaseModel):
    """方案生成会话基础模型"""
    conversation_id: str = Field(..., description="对话会话ID")
    customer_id: str = Field(..., description="客户ID")
    consultant_id: str = Field(..., description="顾问ID")


class PlanGenerationSessionCreate(PlanGenerationSessionBase):
    """创建方案生成会话请求"""
    session_metadata: Optional[Dict[str, Any]] = Field(None, description="会话元数据")


class PlanGenerationSessionInfo(PlanGenerationSessionBase):
    """方案生成会话完整信息"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(..., description="会话ID")
    status: PlanSessionStatus = Field(..., description="会话状态")
    required_info: Dict[str, List[str]] = Field(..., description="必需信息清单")
    extracted_info: Optional[ExtractedInfo] = Field(None, description="提取的信息")
    interaction_history: List[Dict[str, Any]] = Field(default=[], description="交互历史")
    session_metadata: Optional[Dict[str, Any]] = Field(None, description="会话元数据")
    performance_metrics: Optional[Dict[str, Any]] = Field(None, description="性能指标")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class PlanDraftBase(BaseModel):
    """方案草稿基础模型"""
    session_id: str = Field(..., description="会话ID")
    content: PlanContent = Field(..., description="方案内容")


class PlanDraftCreate(PlanDraftBase):
    """创建方案草稿请求"""
    version: Optional[int] = Field(1, description="版本号")
    parent_version: Optional[int] = Field(None, description="父版本号")
    generation_info: Optional[Dict[str, Any]] = Field(None, description="生成信息")


class PlanDraftInfo(BaseModel):
    """方案草稿完整信息"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(..., description="草稿ID")
    session_id: str = Field(..., description="会话ID")
    version: int = Field(..., description="版本号")
    parent_version: Optional[int] = Field(None, description="父版本号")
    status: PlanDraftStatus = Field(..., description="草稿状态")
    content: PlanContent = Field(..., description="方案内容")
    feedback: Optional[PlanFeedback] = Field(None, description="反馈意见")
    improvements: Optional[Dict[str, Any]] = Field(None, description="改进记录")
    generation_info: Optional[Dict[str, Any]] = Field(None, description="生成信息")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class InfoCompletenessBase(BaseModel):
    """信息完整性基础模型"""
    session_id: str = Field(..., description="会话ID")


class InfoCompletenessCreate(InfoCompletenessBase):
    """创建信息完整性记录请求"""
    pass


class InfoCompletenessInfo(BaseModel):
    """信息完整性完整信息"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(..., description="记录ID")
    session_id: str = Field(..., description="会话ID")
    basic_info_status: InfoStatus = Field(..., description="基础信息状态")
    basic_info_score: float = Field(0.0, description="基础信息评分")
    concerns_status: InfoStatus = Field(..., description="关注点状态")
    concerns_score: float = Field(0.0, description="关注点评分")
    budget_status: InfoStatus = Field(..., description="预算状态")
    budget_score: float = Field(0.0, description="预算评分")
    timeline_status: InfoStatus = Field(..., description="时间安排状态")
    timeline_score: float = Field(0.0, description="时间安排评分")
    medical_history_status: InfoStatus = Field(..., description="病史状态")
    medical_history_score: float = Field(0.0, description="病史评分")
    expectations_status: InfoStatus = Field(..., description="期望状态")
    expectations_score: float = Field(0.0, description="期望评分")
    completeness_score: float = Field(0.0, description="总体完整度评分")
    missing_fields: Optional[Dict[str, Any]] = Field(None, description="缺失字段")
    guidance_questions: Optional[GuidanceQuestions] = Field(None, description="引导问题")
    suggestions: Optional[Dict[str, Any]] = Field(None, description="建议")
    last_analysis_at: datetime = Field(..., description="最后分析时间")
    analysis_version: int = Field(1, description="分析版本")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


# ===== 基础方案Schema =====

class PlanCreate(BaseModel):
    """创建方案请求"""
    consultation_id: str = Field(..., description="咨询ID")
    customer_id: str = Field(..., description="客户ID")
    consultant_id: str = Field(..., description="顾问ID")
    title: str = Field(..., description="方案标题")
    content: Dict[str, Any] = Field(..., description="方案内容")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class PlanUpdate(BaseModel):
    """更新方案请求"""
    title: Optional[str] = Field(default=None, description="方案标题")
    content: Optional[Dict[str, Any]] = Field(default=None, description="方案内容")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class PlanResponse(BaseModel):
    """方案响应"""
    id: str = Field(..., description="方案ID")
    consultation_id: str = Field(..., description="咨询ID")
    customer_id: str = Field(..., description="客户ID")
    consultant_id: str = Field(..., description="顾问ID")
    status: str = Field(..., description="方案状态")
    title: str = Field(..., description="方案标题")
    content: Dict[str, Any] = Field(..., description="方案内容")
    version: int = Field(..., description="版本号")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class PlanListResponse(BaseModel):
    """方案列表响应"""
    plans: List[PlanResponse] = Field(..., description="方案列表")
    total: int = Field(..., description="总数")


# ===== AI辅助方案生成请求/响应Schema =====

class GeneratePlanRequest(BaseModel):
    """生成方案请求"""
    conversation_id: str = Field(..., description="对话会话ID")
    force_generation: bool = Field(False, description="强制生成（即使信息不完整）")
    generation_options: Optional[Dict[str, Any]] = Field(None, description="生成选项")


class OptimizePlanRequest(BaseModel):
    """优化方案请求"""
    draft_id: str = Field(..., description="草稿ID")
    optimization_type: Literal["content", "cost", "timeline", "custom"] = Field(..., description="优化类型")
    requirements: Dict[str, Any] = Field(..., description="优化要求")
    feedback: Optional[Dict[str, Any]] = Field(None, description="反馈信息")


class AnalyzeInfoRequest(BaseModel):
    """分析信息请求"""
    conversation_id: str = Field(..., description="对话会话ID")
    force_analysis: bool = Field(False, description="强制分析")


class GenerateGuidanceRequest(BaseModel):
    """生成引导问题请求"""
    session_id: str = Field(..., description="会话ID")
    focus_areas: List[str] = Field(default=[], description="重点关注领域")
    max_questions: int = Field(5, description="最大问题数")
    # 兼容旧端点参数
    conversation_id: Optional[str] = Field(None, description="对话会话ID")
    missing_categories: Optional[List[str]] = Field(None, description="缺失类别")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文")


class PlanGenerationResponse(BaseModel):
    """方案生成响应"""
    session_id: str = Field(..., description="会话ID")
    draft_id: str = Field(..., description="草稿ID")
    status: PlanSessionStatus = Field(..., description="会话状态")
    draft_status: PlanDraftStatus = Field(..., description="草稿状态")
    message: str = Field(..., description="响应消息")
    needs_review: bool = Field(False, description="是否需要审核")
    next_steps: List[str] = Field(default=[], description="下一步操作")


class InfoAnalysisResponse(BaseModel):
    """信息分析响应"""
    session_id: str = Field(..., description="会话ID")
    completeness_score: float = Field(..., description="完整度评分")
    missing_categories: List[str] = Field(default=[], description="缺失类别")
    suggestions: List[str] = Field(default=[], description="建议")
    can_generate_plan: bool = Field(..., description="是否可以生成方案")
    guidance_questions: Optional[GuidanceQuestions] = Field(None, description="引导问题")


class PlanVersionCompareResponse(BaseModel):
    """方案版本对比响应"""
    draft_id: str = Field(..., description="草稿ID")
    current_version: int = Field(..., description="当前版本")
    compare_version: int = Field(..., description="对比版本")
    differences: List[Dict[str, Any]] = Field(default=[], description="差异列表")
    improvement_summary: str = Field(..., description="改进摘要")
