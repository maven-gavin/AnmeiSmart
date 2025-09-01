from sqlalchemy import Column, String, Integer, Float, Text, JSON, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
import enum

from app.common.infrastructure.db.base_model import BaseModel
from app.common.infrastructure.db.uuid_utils import generate_uuid


class PlanStatusEnum(enum.Enum):
    """方案状态枚举"""
    DRAFT = "DRAFT"
    SHARED = "SHARED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class ProjectType(BaseModel):
    """项目类型模型 - 存储可用的医美项目类型"""
    __tablename__ = "project_types"
    __table_args__ = {"comment": "项目类型表，存储医美项目类型和参数配置"}

    id = Column(String(36), primary_key=True, default=generate_uuid, comment="项目类型ID")
    name = Column(String(100), unique=True, nullable=False, comment="项目类型名称")
    label = Column(String(100), nullable=False, comment="项目类型显示名称")
    description = Column(Text, nullable=True, comment="项目类型描述")
    parameters = Column(JSON, nullable=True, comment="项目参数配置（JSON格式）")
    is_active = Column(Boolean, default=True, comment="是否激活")
    category = Column(String(50), nullable=True, comment="项目分类")
    
    # 关联
    simulation_images = relationship("SimulationImage", back_populates="project_type")


class SimulationImage(BaseModel):
    """术前模拟图像模型"""
    __tablename__ = "simulation_images"
    __table_args__ = {"comment": "术前模拟图像表，存储客户的模拟图像"}

    id = Column(String(36), primary_key=True, default=generate_uuid, comment="模拟图像ID")
    customer_id = Column(String(36), ForeignKey("customers.user_id"), nullable=False, comment="客户ID")
    customer_name = Column(String(100), nullable=False, comment="客户姓名")
    original_image_path = Column(String(500), nullable=False, comment="原始图像路径")
    simulated_image_path = Column(String(500), nullable=False, comment="模拟图像路径")
    project_type_id = Column(String(36), ForeignKey("project_types.id"), nullable=False, comment="项目类型ID")
    parameters = Column(JSON, nullable=True, comment="模拟参数（JSON格式）")
    notes = Column(Text, nullable=True, comment="备注")
    consultant_id = Column(String(36), ForeignKey("consultants.user_id"), nullable=False, comment="顾问ID")
    
    # 关联
    project_type = relationship("ProjectType", back_populates="simulation_images")
    customer = relationship("Customer", foreign_keys=[customer_id])
    consultant = relationship("Consultant", foreign_keys=[consultant_id])


class PersonalizedPlan(BaseModel):
    """个性化方案模型"""
    __tablename__ = "personalized_plans"
    __table_args__ = {"comment": "个性化方案表，存储为客户定制的医美方案"}

    id = Column(String(36), primary_key=True, default=generate_uuid, comment="方案ID")
    customer_id = Column(String(36), ForeignKey("customers.user_id"), nullable=False, comment="客户ID")
    customer_name = Column(String(100), nullable=False, comment="客户姓名")
    consultant_id = Column(String(36), ForeignKey("consultants.user_id"), nullable=False, comment="顾问ID")
    consultant_name = Column(String(100), nullable=False, comment="顾问姓名")
    
    # 客户画像
    customer_profile = Column(JSON, nullable=True, comment="客户画像信息（JSON格式）")
    
    # 方案内容
    projects = Column(JSON, nullable=False, comment="推荐项目列表（JSON格式）")
    total_cost = Column(Float, default=0.0, comment="总费用")
    estimated_timeframe = Column(String(100), nullable=True, comment="预计时间框架")
    
    # 方案状态
    status = Column(Enum(PlanStatusEnum), default=PlanStatusEnum.DRAFT, comment="方案状态")
    notes = Column(Text, nullable=True, comment="方案备注")
    
    # 关联
    customer = relationship("Customer", foreign_keys=[customer_id])
    consultant = relationship("Consultant", foreign_keys=[consultant_id])
    plan_versions = relationship("PlanVersion", back_populates="plan", cascade="all, delete-orphan")


class PlanVersion(BaseModel):
    """方案版本模型 - 用于追踪方案的历史版本"""
    __tablename__ = "plan_versions"
    __table_args__ = {"comment": "方案版本表，存储方案的历史版本"}

    id = Column(String(36), primary_key=True, default=generate_uuid, comment="版本ID")
    plan_id = Column(String(36), ForeignKey("personalized_plans.id"), nullable=False, comment="方案ID")
    version_number = Column(Integer, nullable=False, comment="版本号")
    projects = Column(JSON, nullable=False, comment="项目列表快照（JSON格式）")
    total_cost = Column(Float, nullable=False, comment="总费用快照")
    notes = Column(Text, nullable=True, comment="版本备注")
    
    # 关联
    plan = relationship("PersonalizedPlan", back_populates="plan_versions")


class ProjectTemplate(BaseModel):
    """项目模板模型 - 存储标准化的项目模板"""
    __tablename__ = "project_templates"
    __table_args__ = {"comment": "项目模板表，存储标准化的医美项目模板"}

    id = Column(String(36), primary_key=True, default=generate_uuid, comment="模板ID")
    name = Column(String(100), nullable=False, comment="项目名称")
    description = Column(Text, nullable=True, comment="项目描述")
    category = Column(String(50), nullable=True, comment="项目分类")
    base_cost = Column(Float, nullable=False, comment="基础费用")
    duration = Column(String(50), nullable=True, comment="持续时间")
    recovery_time = Column(String(50), nullable=True, comment="恢复时间")
    expected_results = Column(Text, nullable=True, comment="预期效果")
    risks = Column(JSON, nullable=True, comment="风险列表（JSON格式）")
    is_active = Column(Boolean, default=True, comment="是否激活")
    
    # 适用条件
    suitable_age_min = Column(Integer, nullable=True, comment="适用最小年龄")
    suitable_age_max = Column(Integer, nullable=True, comment="适用最大年龄")
    suitable_concerns = Column(JSON, nullable=True, comment="适用关注问题（JSON格式）")


class CustomerPreference(BaseModel):
    """客户偏好模型 - 存储客户的偏好设置"""
    __tablename__ = "customer_preferences"
    __table_args__ = {"comment": "客户偏好表，存储客户的个性化偏好"}

    id = Column(String(36), primary_key=True, default=generate_uuid, comment="偏好ID")
    customer_id = Column(String(36), ForeignKey("customers.user_id"), unique=True, nullable=False, comment="客户ID")
    
    # 偏好设置
    preferred_budget_min = Column(Float, nullable=True, comment="最小预算偏好")
    preferred_budget_max = Column(Float, nullable=True, comment="最大预算偏好")
    preferred_recovery_time = Column(String(50), nullable=True, comment="偏好恢复时间")
    preferred_project_categories = Column(JSON, nullable=True, comment="偏好项目分类（JSON格式）")
    concerns_history = Column(JSON, nullable=True, comment="历史关注问题（JSON格式）")
    
    # 风险承受度
    risk_tolerance = Column(String(20), default="medium", comment="风险承受度(low/medium/high)")
    
    # 关联
    customer = relationship("Customer", foreign_keys=[customer_id]) 