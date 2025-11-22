from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict
from app.core.config import get_settings

# 获取配置
settings = get_settings()


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


class AgentConfigCreate(BaseModel):
    """创建Agent配置的Schema"""
    environment: str = Field(..., description="环境名称（dev/test/prod）", min_length=1, max_length=100)
    appId: str = Field(..., description="应用ID", min_length=1, max_length=255)
    appName: str = Field(..., description="应用名称", min_length=1, max_length=255)
    agentType: Optional[str] = Field(None, description="智能体类型（chat/agent/workflow）")
    apiKey: str = Field(..., description="API密钥", min_length=1)
    baseUrl: str = Field(default_factory=lambda: settings.AGENT_DEFAULT_BASE_URL, description="Agent API基础URL")
    timeoutSeconds: int = Field(default_factory=lambda: settings.AGENT_DEFAULT_TIMEOUT, description="请求超时时间（秒）", ge=1, le=300)
    maxRetries: int = Field(default_factory=lambda: settings.AGENT_DEFAULT_MAX_RETRIES, description="最大重试次数", ge=1, le=10)
    enabled: bool = Field(True, description="是否启用配置")
    description: Optional[str] = Field(None, description="配置描述")


class AgentConfigUpdate(BaseModel):
    """更新Agent配置的Schema"""
    environment: Optional[str] = Field(None, description="环境名称（dev/test/prod）", min_length=1, max_length=100)
    appId: Optional[str] = Field(None, description="应用ID", min_length=1, max_length=255)
    appName: Optional[str] = Field(None, description="应用名称", min_length=1, max_length=255)
    agentType: Optional[str] = Field(None, description="智能体类型（chat/agent/workflow）")
    apiKey: Optional[str] = Field(None, description="API密钥", min_length=1)
    baseUrl: Optional[str] = Field(None, description="Agent API基础URL")
    timeoutSeconds: Optional[int] = Field(None, description="请求超时时间（秒）", ge=1, le=300)
    maxRetries: Optional[int] = Field(None, description="最大重试次数", ge=1, le=10)
    enabled: Optional[bool] = Field(None, description="是否启用配置")
    description: Optional[str] = Field(None, description="配置描述")


class AgentConfigInfo(BaseModel):
    """Agent配置信息Schema"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    id: str = Field(..., description="配置ID", alias="id")
    environment: str = Field(..., description="环境名称", alias="environment")
    appId: str = Field(..., description="应用ID", alias="app_id")
    appName: str = Field(..., description="应用名称", alias="app_name")
    agentType: Optional[str] = Field(None, description="智能体类型", alias="agent_type")
    baseUrl: str = Field(..., description="Agent API基础URL", alias="base_url")
    timeoutSeconds: int = Field(30, description="请求超时时间（秒）", alias="timeout_seconds")
    maxRetries: int = Field(3, description="最大重试次数", alias="max_retries")
    enabled: bool = Field(True, description="是否启用配置", alias="enabled")
    description: Optional[str] = Field(None, description="配置描述", alias="description")
    createdAt: datetime = Field(..., description="创建时间", alias="created_at")
    updatedAt: datetime = Field(..., description="更新时间", alias="updated_at")


class AgentConfigResponse(BaseModel):
    """Agent配置响应Schema"""
    success: bool = Field(..., description="操作是否成功")
    data: Optional[AgentConfigInfo] = Field(None, description="Agent配置数据")
    message: str = Field(..., description="响应消息")


class AgentConfigListResponse(BaseModel):
    """Agent配置列表响应Schema"""
    success: bool = Field(..., description="操作是否成功")
    data: List[AgentConfigInfo] = Field(default_factory=list, description="Agent配置列表")
    message: str = Field(..., description="响应消息")


class AgentTestConnectionRequest(BaseModel):
    """测试Agent连接的请求Schema"""
    baseUrl: str = Field(..., description="Agent API基础URL")
    apiKey: str = Field(..., description="API密钥")
    appType: str = Field(..., description="应用类型", pattern="^(chat|agent|workflow)$")     