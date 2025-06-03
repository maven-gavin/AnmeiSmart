from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


class AIChatRequest(BaseModel):
    """AI聊天请求模型"""
    conversation_id: str = Field(..., description="会话ID")
    content: str = Field(..., description="用户消息内容")
    type: Literal["text", "image", "voice"] = Field("text", description="消息类型")


class AIChatResponse(BaseModel):
    """AI聊天响应模型"""
    id: str = Field(..., description="消息ID")
    content: str = Field(..., description="AI回复内容")
    type: Literal["text", "image", "voice"] = Field("text", description="消息类型")
    conversation_id: str = Field(..., description="会话ID")
    sender: Dict[str, Any] = Field(..., description="发送者信息")
    timestamp: datetime = Field(..., description="时间戳")
    is_read: bool = Field(False, description="是否已读")
    is_important: bool = Field(False, description="是否重要")


class AIProviderInfo(BaseModel):
    """AI提供商信息"""
    name: str = Field(..., description="提供商名称")
    display_name: str = Field(..., description="显示名称") 
    is_available: bool = Field(..., description="是否可用")
    capabilities: List[str] = Field(..., description="支持的能力")


class AICapabilitiesResponse(BaseModel):
    """AI能力响应模型"""
    available_providers: List[AIProviderInfo] = Field(..., description="可用的AI提供商")
    default_provider: str = Field(..., description="默认提供商")
    features: List[str] = Field(..., description="支持的功能")


class AIHealthStatus(BaseModel):
    """AI服务健康状态"""
    status: Literal["healthy", "degraded", "unhealthy"] = Field(..., description="服务状态")
    providers: Dict[str, bool] = Field(..., description="各提供商状态")
    last_check: datetime = Field(..., description="最后检查时间")
    message: Optional[str] = Field(None, description="状态消息")


class StandardAIResponse(BaseModel):
    """标准化AI响应格式"""
    id: str = Field(..., description="响应ID")
    content: str = Field(..., description="响应内容")
    timestamp: datetime = Field(..., description="时间戳")
    provider: str = Field(..., description="提供商名称")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class StandardConversationHistory(BaseModel):
    """标准化对话历史格式"""
    messages: List[Dict[str, Any]] = Field(..., description="历史消息")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")


class AIServiceConfig(BaseModel):
    """AI服务配置"""
    provider: str = Field(..., description="提供商名称")
    api_key: str = Field(..., description="API密钥")
    api_base_url: str = Field(..., description="API基础URL")
    model: Optional[str] = Field(None, description="模型名称")
    temperature: Optional[float] = Field(0.7, description="温度系数")
    max_tokens: Optional[int] = Field(2000, description="最大token数")
    is_enabled: bool = Field(True, description="是否启用") 