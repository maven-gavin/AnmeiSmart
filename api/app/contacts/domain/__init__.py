"""
Contact领域层
"""
from .contact_domain_service import ContactDomainService
from .interfaces import IContactRepository, IContactApplicationService, IContactDomainService
from .entities import (
    FriendshipEntity, ContactTagEntity, ContactGroupEntity,
    FriendshipStatus, TagCategory, GroupType, GroupMemberRole, GroupMemberEntity, InteractionRecordEntity
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
    "FriendshipEntity",
    "ContactTagEntity", 
    "ContactGroupEntity",
    
    # 值对象
    "FriendshipStatus",
    "TagCategory",
    "GroupType",
    "GroupMemberRole", 
    "GroupMemberEntity",
    "InteractionRecordEntity",
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
