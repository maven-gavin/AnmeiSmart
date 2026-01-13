from enum import Enum as PyEnum
from sqlalchemy import Column, String, Text, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship, backref

from app.common.models.base_model import BaseModel
from app.common.deps.uuid_utils import profile_id, insight_id

# --- 枚举定义 ---

class InsightCategory(str, PyEnum):
    """画像维度/分类"""
    NEED = "need"              # 核心需求
    BUDGET = "budget"          # 预算能力
    AUTHORITY = "authority"    # 决策权限
    TIMELINE = "timeline"      # 时间表
    PREFERENCE = "preference"  # 个人偏好 (如：喜欢喝茶，反感电话推销)
    RISK = "risk"             # 风险项 (如：竞品介入)
    TRAIT = "trait"           # 性格特质 (如：谨慎、冲动)
    BACKGROUND = "background"  # 背景信息
    OTHER = "other"           # 其他

class InsightSource(str, PyEnum):
    """来源类型"""
    AI_GENERATED = "ai"       # SmartBrain分析生成
    HUMAN_INPUT = "human"     # 销售人工录入

class InsightStatus(str, PyEnum):
    """事实状态"""
    ACTIVE = "active"         # 当前有效 (AI决策主要参考)
    ARCHIVED = "archived"     # 已归档/失效 (历史记录，保留时间线)

# --- 模型定义 ---

class Customer(BaseModel):
    """客户特有信息表，存储客户扩展信息"""
    __tablename__ = "customers"
    __table_args__ = {"comment": "客户表，存储客户扩展信息"}
    
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False, comment="用户ID")
    
    # 关联到基础用户表
    # 使用 backref 自动在 User 模型上创建 customer 属性，避免 User 模型中的循环导入问题
    user = relationship("app.identity_access.models.user.User", 
                       foreign_keys=[user_id], 
                       backref=backref("customer", uselist=False, cascade="all, delete-orphan"))
    
    # 关联到客户档案
    profile = relationship("CustomerProfile", back_populates="customer", uselist=False, cascade="all, delete-orphan")


class CustomerProfile(BaseModel):
    """
    客户核心档案表 (Core Profile)
    定位：静态、结构化、高频筛选
    """
    __tablename__ = "customer_profiles"
    __table_args__ = {"comment": "客户核心档案表，存储结构化销售状态"}

    id = Column(String(36), primary_key=True, default=profile_id, comment="档案ID")
    customer_id = Column(String(36), ForeignKey("customers.user_id"), unique=True, nullable=False, comment="客户用户ID")
    
    # 核心销售维度 (保留少量关键字段用于列表筛选)
    life_cycle_stage = Column(String(50), default="lead", comment="生命周期阶段(lead/prospect/deal/customer)")
    industry = Column(String(100), nullable=True, comment="所属行业")
    company_scale = Column(String(50), nullable=True, comment="公司规模")
    
    # AI 自动生成的置顶摘要 (由 Insight 聚合而成，方便人一眼看懂)
    ai_summary = Column(Text, nullable=True, comment="AI生成的客户全景摘要")
    
    # 扩展字段 (用于存储不常用的结构化数据)
    extra_data = Column(JSON, default=dict, comment="扩展属性")

    # 关联关系
    customer = relationship("Customer", back_populates="profile")
    # 关联画像流
    insights = relationship("CustomerInsight", back_populates="profile", cascade="all, delete-orphan")


class CustomerInsight(BaseModel):
    """
    客户画像/洞察流 (Insights Stream)
    定位：动态、原子化、时间流、混合配置
    说明：这是 SmartBrain 对客户认知的核心存储，像朋友圈一样按时间倒序排列
    """
    __tablename__ = "customer_insights"
    __table_args__ = {"comment": "客户动态画像/洞察表"}

    id = Column(String(36), primary_key=True, default=insight_id, comment="洞察ID")
    profile_id = Column(String(36), ForeignKey("customer_profiles.id"), nullable=False, comment="关联档案ID")
    
    # 核心内容
    category = Column(String(50), nullable=False, default=InsightCategory.OTHER.value, comment="维度分类(预算/需求/偏好等)")
    content = Column(Text, nullable=False, comment="洞察内容/事实描述")
    
    # 来源与权限
    source = Column(String(20), default=InsightSource.AI_GENERATED.value, comment="来源(AI/人工)")
    created_by_name = Column(String(100), nullable=True, comment="创建人姓名(如果是人工录入)")
    
    # 状态管理 (支持新事实覆盖旧事实，但不物理删除)
    status = Column(String(20), default=InsightStatus.ACTIVE.value, comment="状态(active/archived)")
    confidence = Column(Float, default=1.0, comment="置信度(0.0-1.0)")
    
    # 关联关系
    profile = relationship("CustomerProfile", back_populates="insights")

    # 索引建议 (需在数据库迁移文件中添加): 
    # index_profile_status_created (profile_id, status, created_at DESC) -> 用于快速查询某客户的有效画像