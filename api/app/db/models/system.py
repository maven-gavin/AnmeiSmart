from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, Text, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base
import json


class SystemSettings(Base):
    """系统设置数据库模型"""
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    siteName = Column(String(255), nullable=False, default="安美智能咨询系统")
    logoUrl = Column(String(1024), nullable=True, default="/logo.png")
    defaultModelId = Column(String(255), nullable=True)
    maintenanceMode = Column(Boolean, default=False)
    userRegistrationEnabled = Column(Boolean, default=True)
    
    # 关联AI模型配置
    ai_models = relationship("AIModelConfig", back_populates="system_settings", cascade="all, delete-orphan")


class AIModelConfig(Base):
    """AI模型配置数据库模型"""
    __tablename__ = "ai_model_configs"

    id = Column(Integer, primary_key=True, index=True)
    modelName = Column(String(255), nullable=False)
    apiKey = Column(Text, nullable=False)
    baseUrl = Column(String(1024), nullable=False)
    maxTokens = Column(Integer, default=2000)
    temperature = Column(Float, default=0.7)
    enabled = Column(Boolean, default=True)
    
    # 外键关联系统设置
    system_settings_id = Column(Integer, ForeignKey("system_settings.id"))
    system_settings = relationship("SystemSettings", back_populates="ai_models") 