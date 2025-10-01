from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict


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


class AgentConfigCreate(BaseModel):
    """创建Agent配置的Schema"""
    environment: str = Field(..., description="环境名称（dev/test/prod）", min_length=1, max_length=100)
    appId: str = Field(..., description="应用ID", min_length=1, max_length=255)
    appName: str = Field(..., description="应用名称", min_length=1, max_length=255)
    agentType: Optional[str] = Field(None, description="智能体类型（chat/agent/workflow）")
    apiKey: str = Field(..., description="API密钥", min_length=1)
    baseUrl: str = Field("http://localhost/v1", description="Agent API基础URL")
    timeoutSeconds: int = Field(30, description="请求超时时间（秒）", ge=1, le=300)
    maxRetries: int = Field(3, description="最大重试次数", ge=1, le=10)
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
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(..., description="配置ID")
    environment: str = Field(..., description="环境名称")
    appId: str = Field(..., description="应用ID")
    appName: str = Field(..., description="应用名称")
    agentType: Optional[str] = Field(None, description="智能体类型")
    baseUrl: str = Field(..., description="Agent API基础URL")
    timeoutSeconds: int = Field(30, description="请求超时时间（秒）")
    maxRetries: int = Field(3, description="最大重试次数")
    enabled: bool = Field(True, description="是否启用配置")
    description: Optional[str] = Field(None, description="配置描述")
    createdAt: datetime = Field(..., description="创建时间")
    updatedAt: datetime = Field(..., description="更新时间")

    @staticmethod
    def from_model(model) -> "AgentConfigInfo":
        """从ORM模型创建Schema实例"""
        return AgentConfigInfo(
            id=model.id,
            environment=model.environment,
            appId=model.app_id,
            appName=model.app_name,
            agentType=model.agent_type,
            baseUrl=model.base_url,
            timeoutSeconds=model.timeout_seconds,
            maxRetries=model.max_retries,
            enabled=model.enabled,
            description=model.description,
            createdAt=model.created_at,
            updatedAt=model.updated_at
        )


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