from sqlalchemy import Column, String, Boolean, Float, Text, Integer, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime
from typing import Optional

from app.db.models.base_model import BaseModel
from app.db.uuid_utils import system_id, model_id


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
        # 优化常见查询的索引
        Index('idx_ai_model_provider_enabled', 'provider', 'enabled'),
        {"comment": "AI模型配置表，存储AI模型相关配置"}
    )

    id = Column(String(36), primary_key=True, default=model_id, comment="模型配置ID")
    model_name = Column(String(255), nullable=False, comment="模型名称")
    # 存储加密的API密钥
    _encrypted_api_key = Column("api_key", Text, nullable=True, comment="API密钥（加密存储）")
    base_url = Column(String(1024), nullable=True, comment="API基础URL")
    max_tokens = Column(Integer, default=2000, comment="最大Token数")
    temperature = Column(Float, default=0.7, comment="采样温度")
    enabled = Column(Boolean, default=True, nullable=False, comment="是否启用")
    provider = Column(String(255), nullable=False, default="openai", comment="服务商")
    description = Column(Text, nullable=True, comment="模型描述")

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