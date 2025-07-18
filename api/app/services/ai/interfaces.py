"""
AI服务抽象接口定义

本模块定义了统一的AI服务接口，支持多种AI服务提供商的无缝切换。
基于DDD设计，确保业务逻辑与具体AI实现解耦。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import uuid


class AIScenario(Enum):
    """AI使用场景枚举"""
    GENERAL_CHAT = "general_chat"           # 通用聊天
    BEAUTY_PLAN = "beauty_plan"             # 医美方案生成
    CONSULTATION_SUMMARY = "consultation_summary"  # 咨询总结
    SENTIMENT_ANALYSIS = "sentiment_analysis"      # 情感分析
    CUSTOMER_SERVICE = "customer_service"          # 客服支持
    MEDICAL_ADVICE = "medical_advice"              # 医疗建议


class AIProvider(Enum):
    """AI服务提供商枚举"""
    DIFY = "dify"
    OPENAI = "openai"
    CLAUDE = "claude"
    QWEN = "qwen"
    CHATGLM = "chatglm"


class ResponseFormat(Enum):
    """响应格式枚举"""
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"
    STRUCTURED = "structured"


@dataclass
class ChatContext:
    """聊天上下文"""
    user_id: str
    session_id: str
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    user_profile: Optional[Dict[str, Any]] = None
    custom_variables: Optional[Dict[str, Any]] = None
    
    def add_message(self, role: str, content: str):
        """添加消息到历史记录"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })


@dataclass
class AIRequest:
    """统一的AI请求模型"""
    scenario: AIScenario
    message: Union[str, Dict[str, Any]]  # 支持字符串或字典类型的消息
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    context: Optional[ChatContext] = None
    parameters: Optional[Dict[str, Any]] = None
    response_format: ResponseFormat = ResponseFormat.TEXT
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    stream: bool = False
    
    @property
    def cache_key(self) -> str:
        """生成缓存键"""
        # 安全处理message参数，支持字符串和字典类型
        if isinstance(self.message, dict):
            message_hash = hash(str(sorted(self.message.items())))
        else:
            message_hash = hash(str(self.message))
        
        # 安全处理parameters参数
        params_hash = hash(str(self.parameters)) if self.parameters else hash("")
        
        return f"{self.scenario.value}:{message_hash}:{params_hash}"


@dataclass
class AIResponse:
    """统一的AI响应模型"""
    request_id: str
    content: str
    provider: AIProvider
    scenario: AIScenario
    success: bool = True
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    usage: Optional[Dict[str, Any]] = None  # token使用情况
    response_time: Optional[float] = None   # 响应时间(秒)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "request_id": self.request_id,
            "content": self.content,
            "provider": self.provider.value,
            "scenario": self.scenario.value,
            "success": self.success,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "usage": self.usage,
            "response_time": self.response_time,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class PlanResponse(AIResponse):
    """医美方案响应扩展"""
    plan_sections: Optional[List[Dict[str, Any]]] = None
    estimated_cost: Optional[Dict[str, float]] = None
    timeline: Optional[Dict[str, str]] = None
    risks: Optional[List[str]] = None


@dataclass
class SummaryResponse(AIResponse):
    """总结响应扩展"""
    key_points: Optional[List[str]] = None
    action_items: Optional[List[str]] = None
    sentiment_score: Optional[float] = None
    categories: Optional[List[str]] = None


@dataclass
class SentimentResponse(AIResponse):
    """情感分析响应扩展"""
    sentiment_score: float = 0.0  # -1 到 1 之间
    confidence: float = 0.0       # 0 到 1 之间
    emotions: Optional[Dict[str, float]] = None  # 具体情感分析


class AIServiceInterface(ABC):
    """AI服务抽象接口
    
    定义了所有AI服务提供商必须实现的标准接口。
    支持同步和异步调用，提供统一的错误处理和监控。
    """
    
    @abstractmethod
    async def chat(self, request: AIRequest) -> AIResponse:
        """通用聊天接口
        
        Args:
            request: AI请求对象
            
        Returns:
            AI响应对象
            
        Raises:
            AIServiceError: AI服务调用失败
        """
        pass
    
    @abstractmethod
    async def generate_beauty_plan(self, request: AIRequest) -> PlanResponse:
        """生成医美方案
        
        Args:
            request: 包含用户信息和需求的请求对象
            
        Returns:
            包含方案详情的响应对象
        """
        pass
    
    @abstractmethod
    async def summarize_consultation(self, request: AIRequest) -> SummaryResponse:
        """总结咨询内容
        
        Args:
            request: 包含咨询对话的请求对象
            
        Returns:
            包含总结内容的响应对象
        """
        pass
    
    @abstractmethod
    async def analyze_sentiment(self, request: AIRequest) -> SentimentResponse:
        """分析文本情感
        
        Args:
            request: 包含待分析文本的请求对象
            
        Returns:
            包含情感分析结果的响应对象
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            服务健康状态信息
        """
        pass
    
    @abstractmethod
    async def get_provider_info(self) -> Dict[str, Any]:
        """获取提供商信息
        
        Returns:
            提供商详细信息
        """
        pass


class AIServiceError(Exception):
    """AI服务异常基类"""
    
    def __init__(self, message: str, provider: Optional[AIProvider] = None, 
                 error_code: Optional[str] = None, details: Optional[Dict] = None):
        super().__init__(message)
        self.provider = provider
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.now()


class AIProviderUnavailableError(AIServiceError):
    """AI服务提供商不可用异常"""
    pass


class AIRateLimitError(AIServiceError):
    """AI服务速率限制异常"""
    pass


class AIAuthenticationError(AIServiceError):
    """AI服务认证失败异常"""
    pass


class AIValidationError(AIServiceError):
    """AI服务请求验证失败异常"""
    pass 