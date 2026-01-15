"""
渠道身份映射模型

用于将外部渠道的 peer_id（open_id）映射到系统内的 customer(User)。
"""

from sqlalchemy import Column, String, JSON, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.sql import func

from app.common.models.base_model import BaseModel


class ChannelIdentity(BaseModel):
    """渠道身份映射表：channel_type + peer_id -> user_id"""

    __tablename__ = "channel_identities"
    __table_args__ = (
        UniqueConstraint("channel_type", "peer_id", name="uq_channel_identity_type_peer"),
        Index("idx_channel_identity_user_id", "user_id"),
        Index("idx_channel_identity_type_peer", "channel_type", "peer_id"),
        {"comment": "渠道身份映射表：外部 peer_id 映射到系统内 customer(User)"},
    )

    channel_type = Column(String(50), nullable=False, comment="渠道类型：wechat_work, lark, dingtalk 等")
    peer_id = Column(String(255), nullable=False, comment="渠道侧用户唯一标识（peer_id/open_id）")

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="系统内客户用户ID")

    peer_name = Column(String(255), nullable=True, comment="渠道侧昵称/展示名")
    extra_data = Column(JSON, nullable=True, comment="渠道侧原始信息（头像、union_id、扩展字段等）")

    first_seen_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="首次出现时间")
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="最后出现时间")

