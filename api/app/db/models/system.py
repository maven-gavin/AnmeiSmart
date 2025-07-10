from sqlalchemy import Column, String, Boolean, ForeignKey, Float, Text, JSON, Enum, DateTime, Integer, Index, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
import enum
from datetime import datetime
from typing import Optional

from app.db.models.base_model import BaseModel
from app.db.uuid_utils import system_id, model_id


class AgentType(str, enum.Enum):
    """Agent类型枚举"""
    GENERAL_CHAT = "general_chat"           # 通用聊天
    BEAUTY_PLAN = "beauty_plan"             # 医美方案生成
    CONSULTATION = "consultation"           # 咨询总结
    CUSTOMER_SERVICE = "customer_service"   # 客服
    MEDICAL_ADVICE = "medical_advice"       # 医疗建议


class SyncStatus(str, enum.Enum):
    """同步状态枚举"""
    NOT_SYNCED = "not_synced"              # 未同步
    SYNCING = "syncing"                    # 同步中
    SUCCESS = "success"                    # 同步成功
    FAILED = "failed"                      # 同步失败


class DifyConnection(BaseModel):
    """Dify连接配置"""
    __tablename__ = "dify_connections"
    __table_args__ = (
        # 确保同一时间只有一个默认连接
        UniqueConstraint('is_default', name='uq_default_connection'),
        # 为常用查询字段添加索引
        Index('idx_dify_connections_active_default', 'is_active', 'is_default'),
        Index('idx_dify_connections_sync_status', 'sync_status'),
        # URL格式检查约束
        CheckConstraint("api_base_url ~ '^https?://'", name='ck_valid_url_format'),
        {"comment": "Dify实例连接配置表"}
    )

    id = Column(String(36), primary_key=True, default=system_id, comment="连接配置ID")
    name = Column(String(255), nullable=False, comment="连接名称")
    api_base_url = Column(String(1024), nullable=False, comment="Dify API基础URL")
    # 存储加密的API密钥
    _encrypted_api_key = Column("api_key", Text, nullable=False, comment="Dify API密钥（加密存储）")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否为活跃连接")
    is_default = Column(Boolean, default=False, nullable=False, comment="是否为默认连接")
    description = Column(Text, nullable=True, comment="连接描述")
    
    # 连接状态 - 使用枚举替代字符串
    last_sync_at = Column(DateTime, nullable=True, comment="最后同步时间")
    sync_status = Column(Enum(SyncStatus), default=SyncStatus.NOT_SYNCED, nullable=False, comment="同步状态")
    
    # 关联的AI模型配置
    ai_models = relationship("AIModelConfig", back_populates="dify_connection", cascade="all, delete-orphan")

    @hybrid_property
    def api_key(self) -> str:
        """获取解密后的API密钥"""
        if not self._encrypted_api_key:
            return ""
        
        # 延迟导入避免循环依赖
        from app.core.encryption import safe_decrypt_api_key
        return safe_decrypt_api_key(self._encrypted_api_key)

    @api_key.setter
    def api_key(self, value: str) -> None:
        """设置API密钥（自动加密）"""
        if not value:
            self._encrypted_api_key = ""
            return
        
        # 延迟导入避免循环依赖
        from app.core.encryption import encrypt_api_key
        self._encrypted_api_key = encrypt_api_key(value)

    def set_api_key_raw(self, encrypted_value: str) -> None:
        """直接设置已加密的API密钥（用于数据库迁移等场景）"""
        self._encrypted_api_key = encrypted_value

    def get_api_key_encrypted(self) -> str:
        """获取加密的API密钥（用于内部处理）"""
        return self._encrypted_api_key or ""


class SystemSettings(BaseModel):
    """系统设置数据库模型，存储全局系统配置"""
    __tablename__ = "system_settings"
    __table_args__ = {"comment": "系统设置表，存储全局系统配置"}

    id = Column(String(36), primary_key=True, default=system_id, comment="系统设置ID")
    # 统一使用snake_case命名
    site_name = Column(String(255), nullable=False, default="安美智能咨询系统", comment="站点名称")
    logo_url = Column(String(1024), nullable=True, default="/logo.png", comment="站点Logo URL")
    default_model_id = Column(String(255), nullable=True, comment="默认AI模型ID")
    maintenance_mode = Column(Boolean, default=False, nullable=False, comment="维护模式开关")
    user_registration_enabled = Column(Boolean, default=True, nullable=False, comment="是否允许用户注册")


class AIModelConfig(BaseModel):
    """AI模型配置数据库模型，存储AI模型相关配置"""
    __tablename__ = "ai_model_configs"
    __table_args__ = (
        # 复合索引优化常见查询
        Index('idx_ai_model_provider_enabled', 'provider', 'enabled'),
        Index('idx_ai_model_agent_type_default', 'agent_type', 'is_default_for_type'),
        Index('idx_ai_model_dify_connection', 'dify_connection_id'),
        # 确保每种类型只有一个默认模型
        UniqueConstraint('agent_type', 'is_default_for_type', name='uq_default_agent_per_type'),
        {"comment": "AI模型配置表，存储AI模型相关配置"}
    )

    id = Column(String(36), primary_key=True, default=model_id, comment="模型配置ID")
    model_name = Column(String(255), nullable=False, comment="模型名称")
    # 存储加密的API密钥
    _encrypted_api_key = Column("api_key", Text, nullable=True, comment="API密钥（非Dify时必填，加密存储）")
    base_url = Column(String(1024), nullable=True, comment="API基础URL（非Dify时必填）")
    # 修正数据类型
    max_tokens = Column(Integer, default=2000, comment="最大Token数")
    temperature = Column(Float, default=0.7, comment="采样温度")
    enabled = Column(Boolean, default=True, nullable=False, comment="是否启用")
    provider = Column(String(255), nullable=False, default="openai", comment="服务商")
    
    # Dify相关字段
    dify_connection_id = Column(String(36), ForeignKey("dify_connections.id"), nullable=True, comment="Dify连接ID")
    dify_app_id = Column(String(255), nullable=True, comment="Dify应用ID")
    dify_app_name = Column(String(255), nullable=True, comment="Dify应用名称")
    dify_app_mode = Column(String(50), nullable=True, comment="Dify应用模式（agent/workflow/chat）")
    
    # Agent配置
    agent_type = Column(Enum(AgentType), nullable=True, comment="Agent类型，仅Dify使用")
    description = Column(Text, nullable=True, comment="模型描述")
    is_default_for_type = Column(Boolean, default=False, nullable=False, comment="是否为该类型的默认模型")
    
    # 简化关系：移除与SystemSettings的直接关联，AI配置独立管理
    dify_connection = relationship("DifyConnection", back_populates="ai_models")

    @hybrid_property
    def api_key(self) -> Optional[str]:
        """获取解密后的API密钥"""
        if not self._encrypted_api_key:
            return None
        
        # 延迟导入避免循环依赖
        from app.core.encryption import safe_decrypt_api_key
        return safe_decrypt_api_key(self._encrypted_api_key)

    @api_key.setter
    def api_key(self, value: Optional[str]) -> None:
        """设置API密钥（自动加密）"""
        if not value:
            self._encrypted_api_key = None
            return
        
        # 延迟导入避免循环依赖
        from app.core.encryption import encrypt_api_key
        self._encrypted_api_key = encrypt_api_key(value)

    def set_api_key_raw(self, encrypted_value: Optional[str]) -> None:
        """直接设置已加密的API密钥（用于数据库迁移等场景）"""
        self._encrypted_api_key = encrypted_value

    def get_api_key_encrypted(self) -> Optional[str]:
        """获取加密的API密钥（用于内部处理）"""
        return self._encrypted_api_key 