from sqlalchemy import Column, String, Boolean, ForeignKey, Float, Text, JSON
from sqlalchemy.orm import relationship

from app.db.models.base_model import BaseModel
from app.db.uuid_utils import system_id, model_id


class SystemSettings(BaseModel):
    """系统设置数据库模型"""
    __tablename__ = "system_settings"

    id = Column(String(36), primary_key=True, default=system_id)
    siteName = Column(String(255), nullable=False, default="安美智能咨询系统")
    logoUrl = Column(String(1024), nullable=True, default="/logo.png")
    defaultModelId = Column(String(255), nullable=True)
    maintenanceMode = Column(Boolean, default=False)
    userRegistrationEnabled = Column(Boolean, default=True)
    
    # 关联AI模型配置
    ai_models = relationship("AIModelConfig", back_populates="system_settings", cascade="all, delete-orphan")


class AIModelConfig(BaseModel):
    """AI模型配置数据库模型"""
    __tablename__ = "ai_model_configs"

    id = Column(String(36), primary_key=True, default=model_id)
    modelName = Column(String(255), nullable=False)
    apiKey = Column(Text, nullable=False)
    baseUrl = Column(String(1024), nullable=False)
    maxTokens = Column(String, default="2000")
    temperature = Column(Float, default=0.7)
    enabled = Column(Boolean, default=True)
    provider = Column(String(255), nullable=False, default="openai")
    appId = Column(String(255), nullable=True)
    
    # 外键关联系统设置
    system_settings_id = Column(String(36), ForeignKey("system_settings.id"))
    system_settings = relationship("SystemSettings", back_populates="ai_models") 