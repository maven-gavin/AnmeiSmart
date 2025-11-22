"""
联系人服务模块 - 新架构
"""

# 导出控制器
from .controllers import contacts_router

# 导出模型
from .models import (
    Friendship, ContactTag, ContactGroup, 
    ContactGroupMember, FriendshipTag, 
    ContactPrivacySetting, InteractionRecord
)

# 导出服务
from .services import ContactService

__all__ = [
    "contacts_router",
    "Friendship",
    "ContactTag",
    "ContactGroup",
    "ContactGroupMember",
    "FriendshipTag",
    "ContactPrivacySetting",
    "InteractionRecord",
    "ContactService",
]
