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


class DifyConfig(BaseModel):
    """Dify配置数据库模型，支持动态配置Dify应用"""
    __tablename__ = "dify_configs"
    __table_args__ = (
        Index('idx_dify_config_enabled', 'enabled'),
        {"comment": "Dify配置表，存储Dify应用配置"}
    )

    id = Column(String(36), primary_key=True, default=model_id, comment="Dify配置ID")
    config_name = Column(String(255), nullable=False, comment="配置名称")
    base_url = Column(String(1024), nullable=False, default="http://localhost/v1", comment="Dify API基础URL")
    
    # Chat应用配置
    chat_app_id = Column(String(255), nullable=True, comment="聊天应用ID")
    _encrypted_chat_api_key = Column("chat_api_key", Text, nullable=True, comment="聊天应用API密钥（加密存储）")
    
    # Beauty Agent配置
    beauty_app_id = Column(String(255), nullable=True, comment="医美方案专家应用ID")
    _encrypted_beauty_api_key = Column("beauty_api_key", Text, nullable=True, comment="医美方案专家API密钥（加密存储）")
    
    # Summary Workflow配置
    summary_app_id = Column(String(255), nullable=True, comment="咨询总结工作流应用ID")
    _encrypted_summary_api_key = Column("summary_api_key", Text, nullable=True, comment="咨询总结工作流API密钥（加密存储）")
    
    enabled = Column(Boolean, default=True, nullable=False, comment="是否启用")
    description = Column(Text, nullable=True, comment="配置描述")
    timeout_seconds = Column(Integer, default=30, comment="请求超时时间（秒）")
    max_retries = Column(Integer, default=3, comment="最大重试次数")

    @hybrid_property
    def chat_api_key(self) -> Optional[str]:
        """获取解密后的聊天API密钥"""
        if not self._encrypted_chat_api_key:
            return None
        from app.core.encryption import safe_decrypt_api_key
        return safe_decrypt_api_key(self._encrypted_chat_api_key)

    @chat_api_key.setter
    def chat_api_key(self, value: Optional[str]) -> None:
        """设置聊天API密钥（自动加密）"""
        if not value:
            self._encrypted_chat_api_key = None
            return
        from app.core.encryption import encrypt_api_key
        self._encrypted_chat_api_key = encrypt_api_key(value)

    @hybrid_property
    def beauty_api_key(self) -> Optional[str]:
        """获取解密后的医美方案专家API密钥"""
        if not self._encrypted_beauty_api_key:
            return None
        from app.core.encryption import safe_decrypt_api_key
        return safe_decrypt_api_key(self._encrypted_beauty_api_key)

    @beauty_api_key.setter
    def beauty_api_key(self, value: Optional[str]) -> None:
        """设置医美方案专家API密钥（自动加密）"""
        if not value:
            self._encrypted_beauty_api_key = None
            return
        from app.core.encryption import encrypt_api_key
        self._encrypted_beauty_api_key = encrypt_api_key(value)

    @hybrid_property
    def summary_api_key(self) -> Optional[str]:
        """获取解密后的咨询总结工作流API密钥"""
        if not self._encrypted_summary_api_key:
            return None
        from app.core.encryption import safe_decrypt_api_key
        return safe_decrypt_api_key(self._encrypted_summary_api_key)

    @summary_api_key.setter
    def summary_api_key(self, value: Optional[str]) -> None:
        """设置咨询总结工作流API密钥（自动加密）"""
        if not value:
            self._encrypted_summary_api_key = None
            return
        from app.core.encryption import encrypt_api_key
        self._encrypted_summary_api_key = encrypt_api_key(value) 