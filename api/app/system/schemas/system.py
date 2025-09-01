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





class SystemSettings(BaseModel):
    """系统设置Schema"""
    siteName: str = Field(..., description="站点名称")
    logoUrl: Optional[str] = Field(None, description="站点Logo URL")

    defaultModelId: Optional[str] = Field(None, description="默认AI模型ID")
    maintenanceMode: bool = Field(False, description="维护模式开关")
    userRegistrationEnabled: bool = Field(True, description="是否允许用户注册")


class SystemSettingsResponse(BaseModel):
    """系统设置响应Schema"""
    success: bool = Field(..., description="操作是否成功")
    data: Optional[SystemSettings] = Field(None, description="系统设置数据")
    message: str = Field(..., description="响应消息")




