from sqlalchemy import Column, String, Boolean, Float, Text, Integer, Index, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime
from typing import Optional

from app.common.infrastructure.db.base_model import BaseModel
from app.common.infrastructure.db.uuid_utils import generate_agent_id

class AgentConfig(BaseModel):
    """Agent配置数据库模型，每个应用作为独立的配置记录"""
    __tablename__ = "agent_configs"
    __table_args__ = (
        Index('idx_agent_config_environment', 'environment'),
        Index('idx_agent_config_enabled', 'enabled'),
        Index('idx_agent_config_env_app', 'environment', 'app_id', unique=True),
        {"comment": "Agent配置表，存储独立的Agent应用配置"}
    )

    id = Column(String(36), primary_key=True, default=generate_agent_id, comment="Agent配置ID")
    environment = Column(String(100), nullable=False, comment="环境名称（dev/test/prod）")
    app_id = Column(String(255), nullable=False, comment="应用ID")
    app_name = Column(String(255), nullable=False, comment="应用名称")
    _encrypted_api_key = Column("api_key", Text, nullable=False, comment="API密钥（加密存储）")
    base_url = Column(String(1024), nullable=False, default="http://localhost/v1", comment="Agent API基础URL")
    timeout_seconds = Column(Integer, default=30, nullable=False, comment="请求超时时间（秒）")
    max_retries = Column(Integer, default=3, nullable=False, comment="最大重试次数")
    enabled = Column(Boolean, default=True, nullable=False, comment="是否启用配置")
    description = Column(Text, nullable=True, comment="配置描述")
    
    # 智能体类型和能力
    agent_type = Column(String(100), nullable=True, comment="智能体类型")
    capabilities = Column(JSON, nullable=True, comment="智能体能力配置")

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