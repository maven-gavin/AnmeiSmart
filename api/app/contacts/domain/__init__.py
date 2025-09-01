"""
Contact领域层
"""
from .contact_domain_service import ContactDomainService
from .interfaces import IContactRepository, IContactApplicationService, IContactDomainService
from .entities import (
    Friendship, ContactTag, ContactGroup,
    FriendshipStatus, TagCategory, GroupType, GroupMemberRole, GroupMember, InteractionRecord
)
from .value_objects import (
    Color, Nickname, TagName, GroupName, Description, Icon, DisplayOrder,
    UsageCount, MemberCount, VerificationMessage, Source, PrivacySettings,
    SearchQuery, Pagination, SortOrder
)

__all__ = [
    # 领域服务
    "ContactDomainService",
    "IContactRepository", 
    "IContactApplicationService",
    "IContactDomainService",
    
    # 聚合根和实体
    "Friendship",
    "ContactTag", 
    "ContactGroup",
    
    # 值对象
    "FriendshipStatus",
    "TagCategory",
    "GroupType",
    "GroupMemberRole", 
    "GroupMember",
    "InteractionRecord",
    "Color",
    "Nickname",
    "TagName",
    "GroupName",
    "Description",
    "Icon",
    "DisplayOrder",
    "UsageCount",
    "MemberCount",
    "VerificationMessage",
    "Source",
    "PrivacySettings",
    "SearchQuery",
    "Pagination",
    "SortOrder",
]
