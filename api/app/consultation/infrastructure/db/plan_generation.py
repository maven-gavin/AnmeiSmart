from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, JSON, Integer, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.common.infrastructure.db.base_model import BaseModel
from app.common.infrastructure.db.uuid_utils import generate_uuid


class PlanGenerationSession(BaseModel):
    """方案生成会话数据库模型，管理整个方案生成的生命周期"""
    __tablename__ = "plan_generation_sessions"
    __table_args__ = {"comment": "方案生成会话表，管理整个方案生成的生命周期"}

    id = Column(String(36), primary_key=True, default=generate_uuid, comment="会话ID")
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True, comment="关联的对话会话ID")
    customer_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True, comment="客户ID")
    consultant_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True, comment="顾问ID")
    
    # 会话状态管理
    status = Column(Enum("collecting", "generating", "optimizing", "reviewing", "completed", "failed", "cancelled", name="plan_session_status"), 
                   default="collecting", nullable=False, index=True, comment="会话状态：收集中、生成中、优化中、审核中、已完成、失败、已取消")
    
    # 必需信息清单 - 定义生成方案所需的信息类型
    required_info = Column(JSON, nullable=False, default=lambda: {
        "basic_info": ["age", "gender", "skin_type", "medical_history"],
        "concerns": ["primary_concern", "secondary_concerns", "severity_level"],
        "budget": ["budget_range", "payment_preference"],
        "timeline": ["preferred_start_date", "availability", "urgency_level"],
        "expectations": ["desired_outcome", "previous_experience", "risk_tolerance"]
    }, comment="必需信息清单，定义生成方案所需的信息类型")
    
    # 从对话中提取的信息
    extracted_info = Column(JSON, nullable=True, comment="""
    从对话中提取的结构化信息 JSON格式:
    {
        "basic_info": {
            "age": 25,
            "gender": "female",
            "skin_type": "combination",
            "medical_history": ["acne", "sensitive_skin"]
        },
        "concerns": {
            "primary_concern": "acne_scars",
            "secondary_concerns": ["fine_lines", "dark_spots"],
            "severity_level": "moderate",
            "affected_areas": ["cheeks", "forehead"]
        },
        "budget": {
            "budget_range": "10000-20000",
            "payment_preference": "installment",
            "flexibility": "moderate"
        },
        "timeline": {
            "preferred_start_date": "2024-02-01",
            "availability": "weekends",
            "urgency_level": "normal"
        },
        "expectations": {
            "desired_outcome": "clear_smooth_skin",
            "previous_experience": "none",
            "risk_tolerance": "low"
        },
        "additional_notes": "特殊要求或备注",
        "extraction_confidence": 0.85,
        "last_updated": "2024-01-01T10:30:00Z"
    }
    """)
    
    # 交互历史记录
    interaction_history = Column(JSON, nullable=True, default=list, comment="""
    人机交互历史记录 JSON格式:
    [
        {
            "timestamp": "2024-01-01T09:00:00Z",
            "action": "session_started",
            "actor": "consultant",
            "actor_id": "consultant_id",
            "details": {"trigger": "manual", "context": "customer_inquiry"}
        },
        {
            "timestamp": "2024-01-01T09:05:00Z",
            "action": "info_extraction_completed",
            "actor": "ai",
            "actor_id": "info_extraction_agent",
            "details": {"extracted_fields": ["age", "concerns"], "confidence": 0.8}
        },
        {
            "timestamp": "2024-01-01T09:10:00Z",
            "action": "guidance_provided",
            "actor": "ai",
            "actor_id": "guidance_agent",
            "details": {"missing_fields": ["budget", "timeline"], "questions": ["What's your budget range?"]}
        },
        {
            "timestamp": "2024-01-01T09:15:00Z",
            "action": "info_provided",
            "actor": "consultant",
            "actor_id": "consultant_id",
            "details": {"method": "direct_input", "fields": ["budget"], "values": {"budget_range": "10000-20000"}}
        }
    ]
    """)
    
    # 会话元数据
    session_metadata = Column(JSON, nullable=True, comment="""
    会话元数据 JSON格式:
    {
        "trigger_source": "chat_command",
        "initial_message_count": 15,
        "ai_model_version": "dify-v1.0",
        "consultant_preferences": {
            "auto_generation": true,
            "review_before_send": true,
            "preferred_style": "detailed"
        },
        "customer_preferences": {
            "communication_style": "detailed",
            "language": "zh-CN"
        },
        "session_config": {
            "max_optimization_rounds": 3,
            "require_medical_review": true,
            "enable_customer_feedback": true
        }
    }
    """)
    
    # 性能指标
    performance_metrics = Column(JSON, nullable=True, comment="""
    性能指标 JSON格式:
    {
        "total_processing_time": 120,  // 秒
        "info_extraction_time": 30,
        "plan_generation_time": 60,
        "optimization_rounds": 2,
        "ai_api_calls": 5,
        "tokens_used": 1500,
        "success_rate": 1.0,
        "quality_score": 0.9
    }
    """)

    # 关联关系
    conversation = relationship("app.chat.infrastructure.db.chat.Conversation", backref="plan_generation_sessions")
    customer = relationship("app.identity_access.infrastructure.db.user.User", foreign_keys=[customer_id], backref="customer_plan_sessions")
    consultant = relationship("app.identity_access.infrastructure.db.user.User", foreign_keys=[consultant_id], backref="consultant_plan_sessions")
    plan_drafts = relationship("app.consultation.infrastructure.db.plan_generation.PlanDraft", back_populates="session", cascade="all, delete-orphan", order_by="app.consultation.infrastructure.db.plan_generation.PlanDraft.version.desc()")
    info_completeness = relationship("app.consultation.infrastructure.db.plan_generation.InfoCompleteness", back_populates="session", uselist=False, cascade="all, delete-orphan")


class PlanDraft(BaseModel):
    """方案草稿数据库模型，存储方案的不同版本"""
    __tablename__ = "plan_drafts"
    __table_args__ = {"comment": "方案草稿表，存储方案的不同版本"}

    id = Column(String(36), primary_key=True, default=generate_uuid, comment="草稿ID")
    session_id = Column(String(36), ForeignKey("plan_generation_sessions.id", ondelete="CASCADE"), nullable=False, index=True, comment="关联的方案生成会话ID")
    
    # 版本管理
    version = Column(Integer, nullable=False, default=1, comment="版本号")
    parent_version = Column(Integer, nullable=True, comment="父版本号（用于版本分支）")
    
    # 草稿状态
    status = Column(Enum("draft", "reviewing", "approved", "rejected", "archived", name="plan_draft_status"), 
                   default="draft", nullable=False, index=True, comment="草稿状态：草稿、审核中、已确认、已拒绝、已归档")
    
    # 方案内容 - 结构化存储
    content = Column(JSON, nullable=False, comment="""
    结构化的方案内容 JSON格式:
    {
        "basic_info": {
            "title": "个性化美肌方案",
            "description": "针对痤疮疤痕和细纹的综合方案",
            "target_concerns": ["acne_scars", "fine_lines"],
            "difficulty_level": "intermediate",
            "total_duration": "3-6个月"
        },
        "analysis": {
            "skin_analysis": "皮肤状态分析",
            "concern_priority": ["acne_scars", "fine_lines", "dark_spots"],
            "treatment_approach": "分阶段治疗",
            "expected_timeline": "6个月"
        },
        "treatment_plan": {
            "phases": [
                {
                    "phase": 1,
                    "name": "基础治疗期",
                    "duration": "1-2个月",
                    "treatments": [
                        {
                            "name": "微针治疗",
                            "frequency": "每月1次",
                            "sessions": 2,
                            "price_per_session": 1200,
                            "total_price": 2400
                        }
                    ]
                }
            ]
        },
        "cost_breakdown": {
            "treatment_costs": 15000,
            "product_costs": 2000,
            "maintenance_costs": 1000,
            "total_cost": 18000,
            "payment_options": ["full_payment", "installment_3", "installment_6"]
        },
        "timeline": {
            "start_date": "2024-02-01",
            "key_milestones": [
                {"date": "2024-02-15", "milestone": "第一次治疗"},
                {"date": "2024-03-15", "milestone": "第二次治疗"},
                {"date": "2024-04-01", "milestone": "第一阶段评估"}
            ],
            "completion_date": "2024-08-01"
        },
        "risks_and_precautions": {
            "potential_risks": ["轻微红肿", "暂时性色素沉着"],
            "contraindications": ["怀孕", "哺乳期"],
            "precautions": ["避免阳光直射", "使用防晒霜"],
            "emergency_contact": "clinic_phone"
        },
        "aftercare": {
            "immediate_care": ["冰敷", "保湿"],
            "long_term_care": ["定期复查", "护肤维护"],
            "product_recommendations": ["温和洁面乳", "修复精华"]
        }
    }
    """)
    
    # 反馈意见
    feedback = Column(JSON, nullable=True, comment="""
    反馈意见 JSON格式:
    {
        "consultant_feedback": {
            "rating": 4,
            "comments": "整体方案合理，建议调整治疗频率",
            "suggestions": ["降低治疗频率", "增加护理产品"],
            "timestamp": "2024-01-01T10:30:00Z",
            "consultant_id": "consultant_id"
        },
        "customer_feedback": {
            "rating": 5,
            "comments": "方案很详细，价格可以接受",
            "concerns": ["治疗时间较长"],
            "preferences": ["周末治疗"],
            "timestamp": "2024-01-01T11:00:00Z",
            "customer_id": "customer_id"
        },
        "medical_review": {
            "approved": true,
            "reviewer": "doctor_id",
            "comments": "医学上可行，注意风险提示",
            "modifications": ["增加过敏测试"],
            "timestamp": "2024-01-01T14:00:00Z"
        }
    }
    """)
    
    # 改进记录
    improvements = Column(JSON, nullable=True, comment="""
    改进记录 JSON格式:
    {
        "version_changes": [
            {
                "change_type": "content_modification",
                "section": "treatment_plan",
                "description": "调整治疗频率从每月2次改为每月1次",
                "reason": "根据顾问建议",
                "timestamp": "2024-01-01T10:45:00Z"
            },
            {
                "change_type": "cost_adjustment",
                "section": "cost_breakdown",
                "description": "增加分期付款选项",
                "reason": "客户要求",
                "timestamp": "2024-01-01T11:15:00Z"
            }
        ],
        "ai_optimization": {
            "optimization_rounds": 2,
            "improvements_made": ["成本优化", "时间调整"],
            "quality_score": 0.9,
            "confidence_level": 0.85
        }
    }
    """)
    
    # 生成信息
    generation_info = Column(JSON, nullable=True, comment="""
    生成信息 JSON格式:
    {
        "generator": "ai",
        "ai_model": "dify-plan-generator-v1.0",
        "generation_method": "template_based",
        "template_used": "comprehensive_beauty_plan",
        "generation_time": 45,  // 秒
        "tokens_used": 800,
        "confidence_score": 0.88,
        "quality_metrics": {
            "completeness": 0.95,
            "consistency": 0.92,
            "feasibility": 0.85
        }
    }
    """)

    # 关联关系
    session = relationship("app.consultation.infrastructure.db.plan_generation.PlanGenerationSession", back_populates="plan_drafts")


class InfoCompleteness(BaseModel):
    """信息完整性数据库模型，跟踪客户信息的完整性状态"""
    __tablename__ = "info_completeness"
    __table_args__ = {"comment": "信息完整性表，跟踪客户信息的完整性状态"}

    id = Column(String(36), primary_key=True, default=generate_uuid, comment="记录ID")
    session_id = Column(String(36), ForeignKey("plan_generation_sessions.id", ondelete="CASCADE"), nullable=False, unique=True, comment="关联的方案生成会话ID")
    
    # 信息类别完整性状态
    basic_info_status = Column(Enum("missing", "partial", "complete", name="info_status"), 
                              default="missing", nullable=False, comment="基础信息状态")
    basic_info_score = Column(Float, default=0.0, comment="基础信息完整度评分 (0-1)")
    
    concerns_status = Column(Enum("missing", "partial", "complete", name="info_status"), 
                            default="missing", nullable=False, comment="关注点信息状态")
    concerns_score = Column(Float, default=0.0, comment="关注点完整度评分 (0-1)")
    
    budget_status = Column(Enum("missing", "partial", "complete", name="info_status"), 
                          default="missing", nullable=False, comment="预算信息状态")
    budget_score = Column(Float, default=0.0, comment="预算完整度评分 (0-1)")
    
    timeline_status = Column(Enum("missing", "partial", "complete", name="info_status"), 
                            default="missing", nullable=False, comment="时间安排状态")
    timeline_score = Column(Float, default=0.0, comment="时间安排完整度评分 (0-1)")
    
    medical_history_status = Column(Enum("missing", "partial", "complete", name="info_status"), 
                                   default="missing", nullable=False, comment="病史信息状态")
    medical_history_score = Column(Float, default=0.0, comment="病史完整度评分 (0-1)")
    
    expectations_status = Column(Enum("missing", "partial", "complete", name="info_status"), 
                                default="missing", nullable=False, comment="期望信息状态")
    expectations_score = Column(Float, default=0.0, comment="期望完整度评分 (0-1)")
    
    # 总体完整性评分
    completeness_score = Column(Float, default=0.0, comment="总体完整度评分 (0-1)")
    
    # 缺失信息详情
    missing_fields = Column(JSON, nullable=True, comment="""
    缺失信息详情 JSON格式:
    {
        "basic_info": {
            "missing": ["age", "skin_type"],
            "partial": ["medical_history"],
            "required": ["age", "gender", "skin_type", "medical_history"]
        },
        "concerns": {
            "missing": ["severity_level"],
            "partial": ["secondary_concerns"],
            "required": ["primary_concern", "secondary_concerns", "severity_level"]
        },
        "budget": {
            "missing": ["budget_range", "payment_preference"],
            "partial": [],
            "required": ["budget_range", "payment_preference"]
        }
    }
    """)
    
    # 引导问题
    guidance_questions = Column(JSON, nullable=True, comment="""
    AI生成的引导问题 JSON格式:
    {
        "basic_info": [
            {
                "field": "age",
                "question": "请问您的年龄是多少？",
                "priority": "high",
                "category": "basic_info"
            }
        ],
        "concerns": [
            {
                "field": "severity_level",
                "question": "您觉得这个问题的严重程度如何？（轻微/中等/严重）",
                "priority": "medium",
                "category": "concerns"
            }
        ],
        "generated_at": "2024-01-01T09:30:00Z",
        "total_questions": 5
    }
    """)
    
    # 建议和提示
    suggestions = Column(JSON, nullable=True, comment="""
    改进建议 JSON格式:
    {
        "next_steps": [
            "询问客户的具体年龄",
            "了解客户的预算范围",
            "确认客户的时间安排"
        ],
        "conversation_tips": [
            "可以先从客户最关心的问题开始询问",
            "预算问题可以放在最后讨论"
        ],
        "auto_suggestions": [
            "基于客户的其他信息，推测年龄可能在25-35岁之间",
            "根据选择的治疗项目，预算可能在10000-20000元"
        ]
    }
    """)
    
    # 最后更新信息
    last_analysis_at = Column(DateTime(timezone=True), server_default=func.now(), comment="最后分析时间")
    analysis_version = Column(Integer, default=1, comment="分析版本号")

    # 关联关系
    session = relationship("app.consultation.infrastructure.db.plan_generation.PlanGenerationSession", back_populates="info_completeness") 