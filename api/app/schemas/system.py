from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, validator
from datetime import datetime


class AIModelConfigInfo(BaseModel):
    """AI模型配置Schema"""
    modelName: str = Field(..., description="模型名称")
    apiKey: Optional[str] = Field(None, description="API密钥")
    baseUrl: Optional[str] = Field(None, description="API基础URL")
    maxTokens: int = Field(2000, description="最大token数")
    temperature: float = Field(0.7, description="温度系数")
    enabled: bool = Field(True, description="是否启用")
    provider: str = Field("openai", description="AI提供商，如openai、dify等")
    
    # Dify相关字段
    dify_connection_id: Optional[str] = Field(None, description="Dify连接ID")
    dify_app_id: Optional[str] = Field(None, description="Dify应用ID")
    dify_app_name: Optional[str] = Field(None, description="Dify应用名称")
    dify_app_mode: Optional[str] = Field(None, description="Dify应用模式")
    
    # Agent配置
    agent_type: Optional[Literal["general_chat", "beauty_plan", "consultation", "customer_service", "medical_advice"]] = Field(None, description="Agent类型")
    description: Optional[str] = Field(None, description="描述")
    is_default_for_type: bool = Field(False, description="是否为该类型默认")
    
    @staticmethod
    def from_model(model) -> "AIModelConfigInfo":
        """从ORM模型转换"""
        return AIModelConfigInfo(
            modelName=model.modelName,
            apiKey=model.apiKey,
            baseUrl=model.baseUrl,
            maxTokens=int(model.maxTokens) if model.maxTokens else 2000,
            temperature=model.temperature,
            enabled=model.enabled,
            provider=model.provider,
            dify_connection_id=model.dify_connection_id,
            dify_app_id=model.dify_app_id,
            dify_app_name=model.dify_app_name,
            dify_app_mode=model.dify_app_mode,
            agent_type=model.agent_type.value if model.agent_type else None,
            description=model.description,
            is_default_for_type=model.is_default_for_type or False
        )


class DifyConnectionCreate(BaseModel):
    """创建Dify连接请求"""
    name: str = Field(..., description="连接名称")
    api_base_url: str = Field(..., description="Dify API基础URL")
    api_key: str = Field(..., description="Dify API密钥")
    description: Optional[str] = Field(None, description="连接描述")
    is_default: bool = Field(False, description="是否设为默认连接")


class DifyConnectionInfo(BaseModel):
    """Dify连接信息"""
    id: str
    name: str
    api_base_url: str
    description: Optional[str]
    is_default: bool
    is_active: bool
    last_sync_at: Optional[datetime]
    sync_status: str
    
    @staticmethod
    def from_model(connection) -> "DifyConnectionInfo":
        """从ORM模型转换"""
        return DifyConnectionInfo(
            id=connection.id,
            name=connection.name,
            api_base_url=connection.api_base_url,
            description=connection.description,
            is_default=connection.is_default,
            is_active=connection.is_active,
            last_sync_at=connection.last_sync_at,
            sync_status=connection.sync_status
        )


class DifyAppInfo(BaseModel):
    """Dify应用信息"""
    id: str
    name: str
    description: str
    mode: str  # agent, workflow, chat, etc.
    status: str
    created_at: Optional[str]
    icon: Optional[str]
    icon_background: Optional[str]
    tags: List[str] = Field(default_factory=list)


class ConfigureAppRequest(BaseModel):
    """配置应用请求"""
    connection_id: str = Field(..., description="Dify连接ID")
    app_id: str = Field(..., description="应用ID")
    app_name: str = Field(..., description="应用名称")
    app_mode: str = Field(..., description="应用模式")
    agent_type: Literal["general_chat", "beauty_plan", "consultation", "customer_service", "medical_advice"]
    description: Optional[str] = Field(None, description="配置描述")
    is_default_for_type: bool = Field(False, description="是否为该类型默认")


class AgentTypeInfo(BaseModel):
    """Agent类型信息"""
    value: str
    label: str
    description: str


class SystemSettings(BaseModel):
    """系统设置Schema"""
    siteName: str = Field("安美智享", description="站点名称")
    logoUrl: str = Field("", description="Logo URL")
    aiModels: List[AIModelConfigInfo] = Field([], description="AI模型配置列表")
    defaultModelId: str = Field("", description="默认AI模型ID")
    maintenanceMode: bool = Field(False, description="是否处于维护模式")
    userRegistrationEnabled: bool = Field(True, description="是否允许用户注册")


class SystemSettingsResponse(BaseModel):
    """系统设置响应Schema"""
    success: bool = Field(True, description="操作是否成功")
    data: SystemSettings = Field(..., description="系统设置数据")
    message: str = Field("", description="消息")


class AIModelConfigCreate(AIModelConfigInfo):
    """创建AI模型配置Schema"""
    pass


class AIModelConfigUpdate(BaseModel):
    """更新AI模型配置Schema"""
    apiKey: Optional[str] = None
    baseUrl: Optional[str] = None
    maxTokens: Optional[int] = None
    temperature: Optional[float] = None
    enabled: Optional[bool] = None
    provider: Optional[str] = None
    dify_connection_id: Optional[str] = None
    dify_app_id: Optional[str] = None
    dify_app_name: Optional[str] = None
    dify_app_mode: Optional[str] = None
    agent_type: Optional[str] = None
    description: Optional[str] = None
    is_default_for_type: Optional[bool] = None
    appId: Optional[str] = None


class AIModelConfigResponse(BaseModel):
    """AI模型配置响应Schema"""
    success: bool = Field(True, description="操作是否成功")
    data: AIModelConfigInfo = Field(..., description="AI模型配置数据")
    message: str = Field("", description="消息")


class AIModelConfigListResponse(BaseModel):
    """AI模型配置列表响应Schema"""
    success: bool = Field(True, description="操作是否成功")
    data: List[AIModelConfigInfo] = Field(..., description="AI模型配置列表")
    message: str = Field("", description="消息")


class SystemSettingsUpdate(BaseModel):
    """更新系统设置Schema"""
    siteName: Optional[str] = None
    logoUrl: Optional[str] = None
    defaultModelId: Optional[str] = None
    maintenanceMode: Optional[bool] = None
    userRegistrationEnabled: Optional[bool] = None 