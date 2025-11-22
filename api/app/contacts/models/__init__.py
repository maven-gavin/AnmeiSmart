"""
通讯录模块数据库模型导出

导出该模块的所有数据库模型，确保SQLAlchemy可以正确建立关系映射。
"""

from .contacts import (
    Friendship,
    ContactTag,
    FriendshipTag,
    ContactGroup,
    ContactGroupMember,
    ContactPrivacySetting,
    InteractionRecord,
)

__all__ = [
    "Friendship",
    "ContactTag",
    "FriendshipTag",
    "ContactGroup",
    "ContactGroupMember",
    "ContactPrivacySetting",
    "InteractionRecord",
]

