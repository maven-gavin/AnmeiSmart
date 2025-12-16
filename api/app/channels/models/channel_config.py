"""
渠道配置模型
"""
from sqlalchemy import Column, String, Boolean, JSON
from app.common.models.base_model import BaseModel


class ChannelConfig(BaseModel):
    """渠道配置表"""
    __tablename__ = "channel_configs"
    __table_args__ = {"comment": "渠道配置表，存储各渠道的配置信息"}

    # id, created_at, updated_at 等字段已由 BaseModel 提供
    channel_type = Column(String(50), nullable=False, comment="渠道类型：wechat_work, wechat, whatsapp等")
    name = Column(String(100), nullable=False, comment="渠道名称")
    config = Column(JSON, nullable=False, comment="渠道配置（API密钥、Webhook URL等）")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")

