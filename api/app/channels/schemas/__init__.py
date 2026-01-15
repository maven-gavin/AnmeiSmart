"""
渠道模块 Schemas
"""

from .channel_identity import ChannelIdentityBindRequest, ChannelIdentityInfo, ChannelCustomerMergeRequest
from .channel_config import ChannelConfigInfo, ChannelConfigUpdate

__all__ = [
    "ChannelIdentityBindRequest",
    "ChannelIdentityInfo",
    "ChannelCustomerMergeRequest",
    "ChannelConfigInfo",
    "ChannelConfigUpdate",
]

