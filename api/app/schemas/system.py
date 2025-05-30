from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class AIModelConfigInfo(BaseModel):
    """AI模型配置Schema"""
    modelName: str = Field(..., description="模型名称")
    apiKey: str = Field(..., description="API密钥")
    baseUrl: str = Field(..., description="API基础URL")
    maxTokens: int = Field(2000, description="最大token数")
    temperature: float = Field(0.7, description="温度系数")
    enabled: bool = Field(True, description="是否启用")
    provider: Optional[str] = Field("openai", description="AI提供商，如openai、dify等")
    appId: Optional[str] = Field(None, description="Dify应用ID")


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