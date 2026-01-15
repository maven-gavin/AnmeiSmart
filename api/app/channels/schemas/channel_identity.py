"""
渠道身份映射相关 Schema
"""

from typing import Any, Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChannelIdentityBindRequest(BaseModel):
    """将某个渠道身份绑定/迁移到指定 customer(User)"""

    channel_type: str = Field(..., min_length=1, max_length=50)
    peer_id: str = Field(..., min_length=1, max_length=255)
    customer_user_id: str = Field(..., min_length=1, max_length=36, description="目标客户用户ID（users.id）")

    peer_name: Optional[str] = Field(None, max_length=255)
    extra_data: Optional[dict[str, Any]] = None

    migrate_conversations: bool = Field(
        True,
        description="是否同步迁移/纠正 tag=channel 会话 owner_id 与元数据（建议开启）",
    )


class ChannelIdentityInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    channel_type: str
    peer_id: str
    user_id: str

    peer_name: Optional[str] = None
    extra_data: Optional[dict[str, Any]] = None

    first_seen_at: datetime
    last_seen_at: datetime


class ChannelCustomerMergeRequest(BaseModel):
    """将 source_customer_user_id 的所有渠道身份合并到 target_customer_user_id"""

    source_customer_user_id: str = Field(..., min_length=1, max_length=36)
    target_customer_user_id: str = Field(..., min_length=1, max_length=36)
    migrate_conversations: bool = Field(True, description="是否同步迁移/纠正相关 tag=channel 会话 owner")

