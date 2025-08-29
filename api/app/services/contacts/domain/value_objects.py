"""
Contact领域值对象
定义Contact领域中的值对象
"""
from typing import Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import re


class FriendshipStatus(Enum):
    """好友关系状态值对象"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    BLOCKED = "blocked"
    DELETED = "deleted"


class TagCategory(Enum):
    """标签分类值对象"""
    WORK = "work"
    PERSONAL = "personal"
    BUSINESS = "business"
    MEDICAL = "medical"
    CUSTOM = "custom"


class GroupType(Enum):
    """分组类型值对象"""
    PERSONAL = "personal"
    WORK = "work"
    PROJECT = "project"
    TEMPORARY = "temporary"


class GroupMemberRole(Enum):
    """分组成员角色值对象"""
    MEMBER = "member"
    ADMIN = "admin"
    OWNER = "owner"


class InteractionType(Enum):
    """交互类型值对象"""
    CHAT_STARTED = "chat_started"
    MESSAGE_SENT = "message_sent"
    CALL_MADE = "call_made"
    MEETING_SCHEDULED = "meeting_scheduled"
    PROFILE_VIEWED = "profile_viewed"
    TAG_ADDED = "tag_added"
    GROUP_ADDED = "group_added"


@dataclass(frozen=True)
class Color:
    """颜色值对象"""
    value: str
    
    def __post_init__(self):
        if not self._is_valid_color(self.value):
            raise ValueError("无效的颜色格式，必须是6位十六进制颜色码")
    
    @staticmethod
    def _is_valid_color(color: str) -> bool:
        """验证颜色格式"""
        return bool(re.match(r"^#[0-9A-Fa-f]{6}$", color))
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Nickname:
    """昵称值对象"""
    value: str
    
    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("昵称不能为空")
        
        if len(self.value.strip()) > 100:
            raise ValueError("昵称不能超过100个字符")
        
        # 更新为清理后的值
        object.__setattr__(self, 'value', self.value.strip())
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class TagName:
    """标签名称值对象"""
    value: str
    
    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("标签名称不能为空")
        
        if len(self.value.strip()) > 50:
            raise ValueError("标签名称不能超过50个字符")
        
        # 更新为清理后的值
        object.__setattr__(self, 'value', self.value.strip())
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class GroupName:
    """分组名称值对象"""
    value: str
    
    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("分组名称不能为空")
        
        if len(self.value.strip()) > 100:
            raise ValueError("分组名称不能超过100个字符")
        
        # 更新为清理后的值
        object.__setattr__(self, 'value', self.value.strip())
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Description:
    """描述值对象"""
    value: Optional[str]
    max_length: int = 500
    
    def __post_init__(self):
        if self.value and len(self.value) > self.max_length:
            raise ValueError(f"描述不能超过{self.max_length}个字符")
    
    def __str__(self) -> str:
        return self.value or ""


@dataclass(frozen=True)
class Icon:
    """图标值对象"""
    value: Optional[str]
    
    def __post_init__(self):
        if self.value and len(self.value) > 50:
            raise ValueError("图标名称不能超过50个字符")
    
    def __str__(self) -> str:
        return self.value or ""


@dataclass(frozen=True)
class DisplayOrder:
    """显示顺序值对象"""
    value: int
    
    def __post_init__(self):
        if self.value < 0:
            raise ValueError("显示顺序不能为负数")
    
    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True)
class UsageCount:
    """使用次数值对象"""
    value: int
    
    def __post_init__(self):
        if self.value < 0:
            raise ValueError("使用次数不能为负数")
    
    def __int__(self) -> int:
        return self.value
    
    def increment(self) -> "UsageCount":
        """增加使用次数"""
        return UsageCount(self.value + 1)
    
    def decrement(self) -> "UsageCount":
        """减少使用次数"""
        if self.value <= 0:
            return UsageCount(0)
        return UsageCount(self.value - 1)


@dataclass(frozen=True)
class MemberCount:
    """成员数量值对象"""
    value: int
    
    def __post_init__(self):
        if self.value < 0:
            raise ValueError("成员数量不能为负数")
    
    def __int__(self) -> int:
        return self.value
    
    def increment(self) -> "MemberCount":
        """增加成员数量"""
        return MemberCount(self.value + 1)
    
    def decrement(self) -> "MemberCount":
        """减少成员数量"""
        if self.value <= 0:
            return MemberCount(0)
        return MemberCount(self.value - 1)


@dataclass(frozen=True)
class InteractionRecord:
    """交互记录值对象"""
    interaction_type: InteractionType
    interaction_time: datetime
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self):
        if not isinstance(self.interaction_type, InteractionType):
            raise ValueError("无效的交互类型")
        
        if not isinstance(self.interaction_time, datetime):
            raise ValueError("交互时间必须是datetime类型")


@dataclass(frozen=True)
class VerificationMessage:
    """验证消息值对象"""
    value: Optional[str]
    max_length: int = 200
    
    def __post_init__(self):
        if self.value and len(self.value) > self.max_length:
            raise ValueError(f"验证消息不能超过{self.max_length}个字符")
    
    def __str__(self) -> str:
        return self.value or ""


@dataclass(frozen=True)
class Source:
    """来源值对象"""
    value: str
    
    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("来源不能为空")
        
        # 更新为清理后的值
        object.__setattr__(self, 'value', self.value.strip())
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class PrivacySettings:
    """隐私设置值对象"""
    profile_visibility: str  # "public", "friends", "private"
    allow_friend_requests: bool
    allow_search_by_phone: bool
    allow_search_by_email: bool
    show_online_status: bool
    show_last_seen: bool
    
    def __post_init__(self):
        valid_visibilities = ["public", "friends", "private"]
        if self.profile_visibility not in valid_visibilities:
            raise ValueError("无效的隐私可见性设置")


@dataclass(frozen=True)
class SearchQuery:
    """搜索查询值对象"""
    value: str
    min_length: int = 1
    max_length: int = 100
    
    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("搜索查询不能为空")
        
        if len(self.value.strip()) < self.min_length:
            raise ValueError(f"搜索查询至少需要{self.min_length}个字符")
        
        if len(self.value.strip()) > self.max_length:
            raise ValueError(f"搜索查询不能超过{self.max_length}个字符")
        
        # 更新为清理后的值
        object.__setattr__(self, 'value', self.value.strip())
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Pagination:
    """分页值对象"""
    page: int
    size: int
    max_size: int = 100
    
    def __post_init__(self):
        if self.page < 1:
            raise ValueError("页码必须大于0")
        
        if self.size < 1:
            raise ValueError("页面大小必须大于0")
        
        if self.size > self.max_size:
            raise ValueError(f"页面大小不能超过{self.max_size}")
    
    @property
    def offset(self) -> int:
        """计算偏移量"""
        return (self.page - 1) * self.size
    
    @property
    def limit(self) -> int:
        """获取限制数量"""
        return self.size


@dataclass(frozen=True)
class SortOrder:
    """排序值对象"""
    field: str
    direction: str  # "asc" or "desc"
    
    def __post_init__(self):
        valid_directions = ["asc", "desc"]
        if self.direction.lower() not in valid_directions:
            raise ValueError("排序方向必须是asc或desc")
        
        # 标准化方向
        object.__setattr__(self, 'direction', self.direction.lower())
    
    @property
    def is_ascending(self) -> bool:
        """是否为升序"""
        return self.direction == "asc"
    
    @property
    def is_descending(self) -> bool:
        """是否为降序"""
        return self.direction == "desc"
