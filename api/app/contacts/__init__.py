"""
Contact服务模块 - DDD架构重构完成
"""
# 导出应用服务层
from .application.contact_application_service import ContactApplicationService

# 导出领域层
from .domain.contact_domain_service import ContactDomainService
from .domain.interfaces import IContactRepository, IContactApplicationService, IContactDomainService
from .domain.entities import (
    FriendshipEntity, ContactTagEntity, ContactGroupEntity,
    FriendshipStatus, TagCategory, GroupType, GroupMemberRole, GroupMemberEntity, InteractionRecordEntity
)
from .domain.value_objects import (
    Color, Nickname, TagName, GroupName, Description, Icon, DisplayOrder,
    UsageCount, MemberCount, VerificationMessage, Source, PrivacySettings,
    SearchQuery, Pagination, SortOrder
)

# 导出基础设施层
from .infrastructure.contact_repository import ContactRepository

# 导出转换器
from .converters.contact_converter import ContactConverter

# 导出集成服务
from .integration.chat_integration_service import ChatIntegrationService


__all__ = [
    # 应用服务层
    "ContactApplicationService",
    
    # 领域层
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
    
    # 基础设施层
    "ContactRepository",
    
    # 转换器
    "ContactConverter",
    
    # 集成服务
    "ChatIntegrationService",
]



