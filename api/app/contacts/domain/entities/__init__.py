"""
Contact领域实体层
"""
from .friendship import FriendshipEntity, FriendshipStatus, InteractionRecordEntity
from .contact_tag import ContactTagEntity, TagCategory
from .contact_group import ContactGroupEntity, GroupType, GroupMemberRole, GroupMemberEntity

__all__ = [
    # 聚合根
    "FriendshipEntity",
    
    # 实体
    "ContactTagEntity",
    "ContactGroupEntity",
    
    # 值对象
    "FriendshipStatus",
    "TagCategory", 
    "GroupType",
    "GroupMemberRole",
    "GroupMemberEntity",
    "InteractionRecordEntity",
]
