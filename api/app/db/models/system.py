from sqlalchemy import Column, String, Boolean, ForeignKey, Float, Text, JSON
from sqlalchemy.orm import relationship

from app.db.models.base_model import BaseModel
from app.db.uuid_utils import system_id, model_id


class SystemSettings(BaseModel):
    """系统设置数据库模型，存储全局系统配置"""
    __tablename__ = "system_settings"
    __table_args__ = {"comment": "系统设置表，存储全局系统配置"}

    id = Column(String(36), primary_key=True, default=system_id, comment="系统设置ID")
    siteName = Column(String(255), nullable=False, default="安美智能咨询系统", comment="站点名称")
    logoUrl = Column(String(1024), nullable=True, default="/logo.png", comment="站点Logo URL")
    defaultModelId = Column(String(255), nullable=True, comment="默认AI模型ID")
    maintenanceMode = Column(Boolean, default=False, comment="维护模式开关")
    userRegistrationEnabled = Column(Boolean, default=True, comment="是否允许用户注册")
    
    # 关联AI模型配置
    ai_models = relationship("AIModelConfig", back_populates="system_settings", cascade="all, delete-orphan")


class AIModelConfig(BaseModel):
    """AI模型配置数据库模型，存储AI模型相关配置"""
    __tablename__ = "ai_model_configs"
    __table_args__ = {"comment": "AI模型配置表，存储AI模型相关配置"}

    id = Column(String(36), primary_key=True, default=model_id, comment="模型配置ID")
    modelName = Column(String(255), nullable=False, comment="模型名称")
    apiKey = Column(Text, nullable=False, comment="API密钥")
    baseUrl = Column(String(1024), nullable=False, comment="API基础URL")
    maxTokens = Column(String, default="2000", comment="最大Token数")
    temperature = Column(Float, default=0.7, comment="采样温度")
    enabled = Column(Boolean, default=True, comment="是否启用")
    provider = Column(String(255), nullable=False, default="openai", comment="服务商")
    appId = Column(String(255), nullable=True, comment="应用ID")
    
    # 外键关联系统设置
    system_settings_id = Column(String(36), ForeignKey("system_settings.id"), comment="系统设置ID")
    system_settings = relationship("SystemSettings", back_populates="ai_models") 