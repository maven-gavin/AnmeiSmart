"""
Schema包初始化
按领域组织各种数据模型的导入
"""

# 聊天领域
from .chat import (
    MessageSender,
    MessageBase,
    MessageCreate,
    MessageCreateRequest,
    AIChatRequest,
    MessageInfo,
    ConversationBase,
    ConversationCreate,
    ConversationInfo,
    # 新增的消息内容结构
    TextMessageContent,
    MediaInfo,
    MediaMessageContent,
    SystemEventContent,
    # 便利函数
    create_text_message_content,
    create_media_message_content,
    create_system_event_content,
)

# 文件领域
from .file import (
    FileInfo,
    FileUploadResponse,
    FileUploadRequest,
    ChunkUploadRequest,
    UploadStatusResponse,
    CompleteUploadRequest,
    ResumableUploadInfo,
    StartResumableUploadRequest,
    StartResumableUploadResponse,
    CancelUploadResponse,
)

# WebSocket领域（目前未使用，保留供将来扩展）
from .websocket import (
    WebSocketMessage,
    WebSocketConnectionInfo,
    WebSocketError,
    WebSocketStats,
)

# AI辅助方案生成领域
from .plan_generation import (
    # 枚举
    PlanSessionStatus,
    PlanDraftStatus,
    InfoStatus,
    # 基础信息结构
    BasicInfo,
    ConcernsInfo,
    BudgetInfo,
    TimelineInfo,
    ExpectationsInfo,
    ExtractedInfo,
    # 方案内容结构
    PlanContent,
    PlanBasicInfo,
    PlanAnalysis,
    TreatmentItem,
    TreatmentPhase,
    TreatmentPlan,
    CostBreakdown,
    PlanTimeline,
    RisksAndPrecautions,
    Aftercare,
    # 反馈结构
    PlanFeedback,
    ConsultantFeedback,
    CustomerFeedback,
    MedicalReview,
    # 引导问题结构
    GuidanceQuestions,
    GuidanceQuestion,
    # 会话相关模型
    PlanGenerationSessionBase,
    PlanGenerationSessionCreate,
    PlanGenerationSessionInfo,
    # 方案草稿模型
    PlanDraftBase,
    PlanDraftCreate,
    PlanDraftInfo,
    # 信息完整性模型
    InfoCompletenessBase,
    InfoCompletenessCreate,
    InfoCompletenessInfo,
    # 请求/响应模型
    GeneratePlanRequest,
    OptimizePlanRequest,
    AnalyzeInfoRequest,
    GenerateGuidanceRequest,
    PlanGenerationResponse,
    InfoAnalysisResponse,
    PlanVersionCompareResponse,
)

# 为了向后兼容，提供一些常用的导入别名
__all__ = [
    # 聊天领域
    "MessageSender",
    "MessageBase", 
    "MessageCreate",
    "MessageCreateRequest",
    "AIChatRequest",
    "MessageInfo",
    "ConversationBase",
    "ConversationCreate", 
    "ConversationInfo",
    # 新增的消息内容结构
    "TextMessageContent",
    "MediaInfo",
    "MediaMessageContent",
    "SystemEventContent",
    # 便利函数
    "create_text_message_content",
    "create_media_message_content",
    "create_system_event_content",
    
    # 文件领域
    "FileInfo",
    "FileUploadResponse",
    "FileUploadRequest",
    "ChunkUploadRequest",
    "UploadStatusResponse", 
    "CompleteUploadRequest",
    "ResumableUploadInfo",
    "StartResumableUploadRequest",
    "StartResumableUploadResponse",
    "CancelUploadResponse",
    
    # WebSocket领域
    "WebSocketMessage",
    "WebSocketConnectionInfo",
    "WebSocketError", 
    "WebSocketStats",
    
    # AI辅助方案生成领域
    "PlanSessionStatus",
    "PlanDraftStatus",
    "InfoStatus",
    "BasicInfo",
    "ConcernsInfo",
    "BudgetInfo",
    "TimelineInfo",
    "ExpectationsInfo",
    "ExtractedInfo",
    "PlanContent",
    "PlanBasicInfo",
    "PlanAnalysis",
    "TreatmentItem",
    "TreatmentPhase",
    "TreatmentPlan",
    "CostBreakdown",
    "PlanTimeline",
    "RisksAndPrecautions",
    "Aftercare",
    "PlanFeedback",
    "ConsultantFeedback",
    "CustomerFeedback",
    "MedicalReview",
    "GuidanceQuestions",
    "GuidanceQuestion",
    "PlanGenerationSessionBase",
    "PlanGenerationSessionCreate",
    "PlanGenerationSessionInfo",
    "PlanDraftBase",
    "PlanDraftCreate",
    "PlanDraftInfo",
    "InfoCompletenessBase",
    "InfoCompletenessCreate",
    "InfoCompletenessInfo",
    "GeneratePlanRequest",
    "OptimizePlanRequest",
    "AnalyzeInfoRequest",
    "GenerateGuidanceRequest",
    "PlanGenerationResponse",
    "InfoAnalysisResponse",
    "PlanVersionCompareResponse",
] 