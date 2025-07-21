from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator, ConfigDict
from datetime import datetime


class SystemSettingsUpdate(BaseModel):
    """系统设置更新Schema"""
    siteName: Optional[str] = Field(None, description="站点名称")
    logoUrl: Optional[str] = Field(None, description="站点Logo URL")
    defaultModelId: Optional[str] = Field(None, description="默认AI模型ID")
    maintenanceMode: Optional[bool] = Field(None, description="维护模式开关")
    userRegistrationEnabled: Optional[bool] = Field(None, description="是否允许用户注册")


class AIModelConfigCreate(BaseModel):
    """创建AI模型配置的Schema"""
    modelName: str = Field(..., description="模型名称", min_length=1, max_length=255)
    provider: str = Field(..., description="服务商", min_length=1, max_length=100)
    apiKey: str = Field(..., description="API密钥", min_length=1)
    baseUrl: Optional[str] = Field(None, description="API基础URL")
    maxTokens: int = Field(2000, description="最大Token数", ge=1, le=100000)
    temperature: float = Field(0.7, description="采样温度", ge=0.0, le=2.0)
    enabled: bool = Field(True, description="是否启用")
    description: Optional[str] = Field(None, description="模型描述", max_length=500)


class AIModelConfigUpdate(BaseModel):
    """更新AI模型配置的Schema"""
    modelName: Optional[str] = Field(None, description="模型名称", min_length=1, max_length=255)
    provider: Optional[str] = Field(None, description="服务商", min_length=1, max_length=100)
    apiKey: Optional[str] = Field(None, description="API密钥", min_length=1)
    baseUrl: Optional[str] = Field(None, description="API基础URL")
    maxTokens: Optional[int] = Field(None, description="最大Token数", ge=1, le=100000)
    temperature: Optional[float] = Field(None, description="采样温度", ge=0.0, le=2.0)
    enabled: Optional[bool] = Field(None, description="是否启用")
    description: Optional[str] = Field(None, description="模型描述", max_length=500)


class AIModelConfigInfo(BaseModel):
    """AI模型配置信息Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(..., description="模型配置ID")
    modelName: str = Field(..., description="模型名称")
    provider: str = Field(..., description="服务商")
    baseUrl: Optional[str] = Field(None, description="API基础URL")
    maxTokens: int = Field(2000, description="最大Token数")
    temperature: float = Field(0.7, description="采样温度")
    enabled: bool = Field(True, description="是否启用")
    description: Optional[str] = Field(None, description="模型描述")
    createdAt: datetime = Field(..., description="创建时间")
    updatedAt: datetime = Field(..., description="更新时间")

    @staticmethod
    def from_model(model) -> "AIModelConfigInfo":
        """从ORM模型创建Schema实例"""
        return AIModelConfigInfo(
            id=model.id,
            modelName=model.model_name,
            provider=model.provider,
            baseUrl=model.base_url,
            maxTokens=model.max_tokens,
            temperature=model.temperature,
            enabled=model.enabled,
            description=model.description,
            createdAt=model.created_at,
            updatedAt=model.updated_at
        )


class SystemSettings(BaseModel):
    """系统设置Schema"""
    siteName: str = Field(..., description="站点名称")
    logoUrl: Optional[str] = Field(None, description="站点Logo URL")
    aiModels: List[AIModelConfigInfo] = Field(default_factory=list, description="AI模型配置列表")
    defaultModelId: Optional[str] = Field(None, description="默认AI模型ID")
    maintenanceMode: bool = Field(False, description="维护模式开关")
    userRegistrationEnabled: bool = Field(True, description="是否允许用户注册")


class SystemSettingsResponse(BaseModel):
    """系统设置响应Schema"""
    success: bool = Field(..., description="操作是否成功")
    data: Optional[SystemSettings] = Field(None, description="系统设置数据")
    message: str = Field(..., description="响应消息")


class AIModelConfigResponse(BaseModel):
    """AI模型配置响应Schema"""
    success: bool = Field(..., description="操作是否成功")
    data: Optional[AIModelConfigInfo] = Field(None, description="AI模型配置数据")
    message: str = Field(..., description="响应消息")


class AIModelConfigListResponse(BaseModel):
    """AI模型配置列表响应Schema"""
    success: bool = Field(..., description="操作是否成功")
    data: List[AIModelConfigInfo] = Field(default_factory=list, description="AI模型配置列表")
    message: str = Field(..., description="响应消息")


class DifyConfigCreate(BaseModel):
    """创建Dify配置的Schema"""
    environment: str = Field(..., description="环境名称（dev/test/prod）", min_length=1, max_length=100)
    appId: str = Field(..., description="应用ID", min_length=1, max_length=255)
    appName: str = Field(..., description="应用名称", min_length=1, max_length=255)
    apiKey: str = Field(..., description="API密钥", min_length=1)
    baseUrl: str = Field("http://localhost/v1", description="Dify API基础URL")
    timeoutSeconds: int = Field(30, description="请求超时时间（秒）", ge=1, le=300)
    maxRetries: int = Field(3, description="最大重试次数", ge=1, le=10)
    enabled: bool = Field(True, description="是否启用配置")
    description: Optional[str] = Field(None, description="配置描述")


class DifyConfigUpdate(BaseModel):
    """更新Dify配置的Schema"""
    environment: Optional[str] = Field(None, description="环境名称（dev/test/prod）", min_length=1, max_length=100)
    appId: Optional[str] = Field(None, description="应用ID", min_length=1, max_length=255)
    appName: Optional[str] = Field(None, description="应用名称", min_length=1, max_length=255)
    apiKey: Optional[str] = Field(None, description="API密钥", min_length=1)
    baseUrl: Optional[str] = Field(None, description="Dify API基础URL")
    timeoutSeconds: Optional[int] = Field(None, description="请求超时时间（秒）", ge=1, le=300)
    maxRetries: Optional[int] = Field(None, description="最大重试次数", ge=1, le=10)
    enabled: Optional[bool] = Field(None, description="是否启用配置")
    description: Optional[str] = Field(None, description="配置描述")


class DifyConfigInfo(BaseModel):
    """Dify配置信息Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(..., description="配置ID")
    environment: str = Field(..., description="环境名称")
    appId: str = Field(..., description="应用ID")
    appName: str = Field(..., description="应用名称")
    baseUrl: str = Field(..., description="Dify API基础URL")
    timeoutSeconds: int = Field(30, description="请求超时时间（秒）")
    maxRetries: int = Field(3, description="最大重试次数")
    enabled: bool = Field(True, description="是否启用配置")
    description: Optional[str] = Field(None, description="配置描述")
    createdAt: datetime = Field(..., description="创建时间")
    updatedAt: datetime = Field(..., description="更新时间")

    @staticmethod
    def from_model(model) -> "DifyConfigInfo":
        """从ORM模型创建Schema实例"""
        return DifyConfigInfo(
            id=model.id,
            environment=model.environment,
            appId=model.app_id,
            appName=model.app_name,
            baseUrl=model.base_url,
            timeoutSeconds=model.timeout_seconds,
            maxRetries=model.max_retries,
            enabled=model.enabled,
            description=model.description,
            createdAt=model.created_at,
            updatedAt=model.updated_at
        )


class DifyConfigResponse(BaseModel):
    """Dify配置响应Schema"""
    success: bool = Field(..., description="操作是否成功")
    data: Optional[DifyConfigInfo] = Field(None, description="Dify配置数据")
    message: str = Field(..., description="响应消息")


class DifyConfigListResponse(BaseModel):
    """Dify配置列表响应Schema"""
    success: bool = Field(..., description="操作是否成功")
    data: List[DifyConfigInfo] = Field(default_factory=list, description="Dify配置列表")
    message: str = Field(..., description="响应消息")


class DifyTestConnectionRequest(BaseModel):
    """测试Dify连接的请求Schema"""
    baseUrl: str = Field(..., description="Dify API基础URL")
    apiKey: str = Field(..., description="API密钥")
    appType: str = Field(..., description="应用类型", pattern="^(chat|agent|workflow)$") 