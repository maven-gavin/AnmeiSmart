from typing import List, Optional
from pydantic import BaseModel, Field


class AIModelConfig(BaseModel):
    """AI模型配置Schema"""
    modelName: str = Field(..., description="模型名称")
    apiKey: str = Field(..., description="API密钥")
    baseUrl: str = Field(..., description="API基础URL")
    maxTokens: int = Field(2000, description="最大Token数")
    temperature: float = Field(0.7, description="温度系数", ge=0, le=2)
    enabled: bool = Field(True, description="是否启用")


class SystemSettings(BaseModel):
    """系统设置Schema"""
    siteName: str = Field(..., description="系统名称")
    logoUrl: str = Field("", description="Logo URL")
    aiModels: List[AIModelConfig] = Field(default_factory=list, description="AI模型配置列表")
    defaultModelId: str = Field("", description="默认AI模型ID")
    maintenanceMode: bool = Field(False, description="维护模式")
    userRegistrationEnabled: bool = Field(True, description="是否允许用户注册")


class SystemSettingsResponse(BaseModel):
    """系统设置响应Schema"""
    success: bool = Field(True, description="操作是否成功")
    data: SystemSettings = Field(..., description="系统设置数据")
    message: str = Field("", description="消息")


class AIModelConfigCreate(BaseModel):
    """创建AI模型配置Schema"""
    modelName: str = Field(..., description="模型名称")
    apiKey: str = Field(..., description="API密钥")
    baseUrl: str = Field(..., description="API基础URL")
    maxTokens: int = Field(2000, description="最大Token数")
    temperature: float = Field(0.7, description="温度系数", ge=0, le=2)
    enabled: bool = Field(True, description="是否启用")


class AIModelConfigUpdate(BaseModel):
    """更新AI模型配置Schema"""
    modelName: Optional[str] = Field(None, description="模型名称")
    apiKey: Optional[str] = Field(None, description="API密钥")
    baseUrl: Optional[str] = Field(None, description="API基础URL")
    maxTokens: Optional[int] = Field(None, description="最大Token数")
    temperature: Optional[float] = Field(None, description="温度系数", ge=0, le=2)
    enabled: Optional[bool] = Field(None, description="是否启用")


class AIModelConfigResponse(BaseModel):
    """AI模型配置响应Schema"""
    success: bool = Field(True, description="操作是否成功")
    data: AIModelConfig = Field(..., description="AI模型配置数据")
    message: str = Field("", description="消息")


class AIModelConfigListResponse(BaseModel):
    """AI模型配置列表响应Schema"""
    success: bool = Field(True, description="操作是否成功")
    data: List[AIModelConfig] = Field(..., description="AI模型配置列表")
    message: str = Field("", description="消息")


class SystemSettingsUpdate(BaseModel):
    """更新系统设置Schema"""
    siteName: Optional[str] = Field(None, description="系统名称")
    logoUrl: Optional[str] = Field(None, description="Logo URL")
    defaultModelId: Optional[str] = Field(None, description="默认AI模型ID")
    maintenanceMode: Optional[bool] = Field(None, description="维护模式")
    userRegistrationEnabled: Optional[bool] = Field(None, description="是否允许用户注册") 