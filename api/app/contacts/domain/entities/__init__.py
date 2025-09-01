"""
Contact领域实体层
"""
from .friendship import Friendship, FriendshipStatus, InteractionRecord
from .contact_tag import ContactTag, TagCategory
from .contact_group import ContactGroup, GroupType, GroupMemberRole, GroupMember

__all__ = [
    # 聚合根
    "Friendship",
    
    # 实体
    "ContactTag",
    "ContactGroup",
    
    # 值对象
    "FriendshipStatus",
    "TagCategory", 
    "GroupType",
    "GroupMemberRole",
    "GroupMember",
    "InteractionRecord",
]
