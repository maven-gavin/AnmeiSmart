"""
通讯录相关的Pydantic模型
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


# 枚举定义
class FriendshipStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    BLOCKED = "blocked"
    DELETED = "deleted"


class TagCategory(str, Enum):
    WORK = "work"
    PERSONAL = "personal"
    BUSINESS = "business"
    MEDICAL = "medical"
    CUSTOM = "custom"


class GroupType(str, Enum):
    PERSONAL = "personal"
    WORK = "work"
    PROJECT = "project"
    TEMPORARY = "temporary"


class GroupMemberRole(str, Enum):
    MEMBER = "member"
    ADMIN = "admin"
    OWNER = "owner"


class InteractionType(str, Enum):
    CHAT_STARTED = "chat_started"
    MESSAGE_SENT = "message_sent"
    CALL_MADE = "call_made"
    MEETING_SCHEDULED = "meeting_scheduled"
    PROFILE_VIEWED = "profile_viewed"
    TAG_ADDED = "tag_added"
    GROUP_ADDED = "group_added"


# 基础模型
class ContactTagBase(BaseModel):
    """联系人标签基础模型"""
    name: str = Field(..., max_length=50, description="标签名称")
    color: str = Field("#3B82F6", pattern=r"^#[0-9A-Fa-f]{6}$", description="标签颜色（HEX格式）")
    icon: Optional[str] = Field(None, max_length=50, description="标签图标")
    description: Optional[str] = Field(None, max_length=200, description="标签描述")
    category: TagCategory = Field(TagCategory.CUSTOM, description="标签分类")
    display_order: int = Field(0, description="显示顺序")
    is_visible: bool = Field(True, description="是否可见")


class ContactTagCreate(ContactTagBase):
    """创建联系人标签请求模型"""
    pass


class ContactTagUpdate(BaseModel):
    """更新联系人标签请求模型"""
    name: Optional[str] = Field(None, max_length=50, description="标签名称")
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$", description="标签颜色（HEX格式）")
    icon: Optional[str] = Field(None, max_length=50, description="标签图标")
    description: Optional[str] = Field(None, max_length=200, description="标签描述")
    category: Optional[TagCategory] = Field(None, description="标签分类")
    display_order: Optional[int] = Field(None, description="显示顺序")
    is_visible: Optional[bool] = Field(None, description="是否可见")


class ContactTagResponse(ContactTagBase):
    """联系人标签响应模型"""
    id: str = Field(..., description="标签ID")
    user_id: str = Field(..., description="创建用户ID")
    is_system_tag: bool = Field(..., description="是否系统预设标签")
    usage_count: int = Field(..., description="使用次数")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# 好友关系模型
class FriendshipBase(BaseModel):
    """好友关系基础模型"""
    nickname: Optional[str] = Field(None, max_length=100, description="给好友设置的昵称")
    remark: Optional[str] = Field(None, description="好友备注")
    is_starred: bool = Field(False, description="是否星标好友")
    is_muted: bool = Field(False, description="是否免打扰")
    is_pinned: bool = Field(False, description="是否置顶显示")


class FriendRequestCreate(BaseModel):
    """发送好友请求模型"""
    friend_id: str = Field(..., description="要添加的好友用户ID")
    verification_message: Optional[str] = Field(None, max_length=200, description="验证消息")
    source: Optional[str] = Field(None, max_length=50, description="添加来源")


class FriendRequestAction(BaseModel):
    """处理好友请求模型"""
    action: str = Field(..., pattern="^(accept|reject)$", description="操作类型：accept/reject")
    message: Optional[str] = Field(None, max_length=200, description="回复消息")


class UpdateFriendshipRequest(FriendshipBase):
    """更新好友关系请求模型"""
    pass


class UserSearchRequest(BaseModel):
    """用户搜索请求模型"""
    query: str = Field(..., min_length=1, max_length=100, description="搜索关键词")
    search_type: Optional[str] = Field("all", pattern="^(all|phone|email|username)$", description="搜索类型")
    limit: int = Field(10, ge=1, le=50, description="返回结果数量限制")


class UserSearchResult(BaseModel):
    """用户搜索结果模型"""
    id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    avatar: Optional[str] = Field(None, description="头像URL")
    roles: List[str] = Field(..., description="用户角色列表")
    is_friend: bool = Field(..., description="是否已经是好友")
    friendship_status: Optional[FriendshipStatus] = Field(None, description="好友关系状态")

    class Config:
        from_attributes = True


class FriendshipResponse(FriendshipBase):
    """好友关系响应模型"""
    id: str = Field(..., description="好友关系ID")
    user_id: str = Field(..., description="用户ID")
    friend_id: str = Field(..., description="好友用户ID")
    status: FriendshipStatus = Field(..., description="好友状态")
    source: Optional[str] = Field(None, description="添加来源")
    is_blocked: bool = Field(..., description="是否已屏蔽")
    requested_at: datetime = Field(..., description="请求时间")
    accepted_at: Optional[datetime] = Field(None, description="接受时间")
    last_interaction_at: Optional[datetime] = Field(None, description="最后互动时间")
    interaction_count: int = Field(..., description="互动次数")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    # 关联数据
    friend: Optional[Dict[str, Any]] = Field(None, description="好友用户信息")
    tags: List[ContactTagResponse] = Field([], description="关联的标签列表")

    class Config:
        from_attributes = True


class FriendRequestResponse(BaseModel):
    """好友请求响应模型"""
    id: str = Field(..., description="好友关系ID")
    user_id: str = Field(..., description="发送请求的用户ID")
    friend_id: str = Field(..., description="接收请求的用户ID")
    status: FriendshipStatus = Field(..., description="请求状态")
    verification_message: Optional[str] = Field(None, description="验证消息")
    source: Optional[str] = Field(None, description="添加来源")
    requested_at: datetime = Field(..., description="请求时间")
    
    # 关联用户信息
    user: Optional[Dict[str, Any]] = Field(None, description="发送请求的用户信息")
    friend: Optional[Dict[str, Any]] = Field(None, description="接收请求的用户信息")

    class Config:
        from_attributes = True


# 分组管理模型
class ContactGroupBase(BaseModel):
    """联系人分组基础模型"""
    name: str = Field(..., max_length=100, description="分组名称")
    description: Optional[str] = Field(None, description="分组描述")
    avatar: Optional[str] = Field(None, max_length=1024, description="分组头像URL")
    group_type: GroupType = Field(GroupType.PERSONAL, description="分组类型")
    color_theme: str = Field("#3B82F6", pattern=r"^#[0-9A-Fa-f]{6}$", description="分组主题色")
    display_order: int = Field(0, description="显示顺序")
    is_collapsed: bool = Field(False, description="是否折叠显示")
    max_members: Optional[int] = Field(None, ge=1, description="最大成员数（可选限制）")
    is_private: bool = Field(False, description="是否私有分组")


class CreateContactGroupRequest(ContactGroupBase):
    """创建联系人分组请求模型"""
    pass


class UpdateContactGroupRequest(BaseModel):
    """更新联系人分组请求模型"""
    name: Optional[str] = Field(None, max_length=100, description="分组名称")
    description: Optional[str] = Field(None, description="分组描述")
    avatar: Optional[str] = Field(None, max_length=1024, description="分组头像URL")
    group_type: Optional[GroupType] = Field(None, description="分组类型")
    color_theme: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$", description="分组主题色")
    display_order: Optional[int] = Field(None, description="显示顺序")
    is_collapsed: Optional[bool] = Field(None, description="是否折叠显示")
    max_members: Optional[int] = Field(None, ge=1, description="最大成员数（可选限制）")
    is_private: Optional[bool] = Field(None, description="是否私有分组")


class ContactGroupResponse(ContactGroupBase):
    """联系人分组响应模型"""
    id: str = Field(..., description="分组ID")
    user_id: str = Field(..., description="创建用户ID")
    member_count: int = Field(..., description="当前成员数")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    # 可选的成员信息
    members: Optional[List[Dict[str, Any]]] = Field(None, description="分组成员列表")

    class Config:
        from_attributes = True


class UpdateGroupMembersRequest(BaseModel):
    """更新分组成员请求模型"""
    add_friendship_ids: List[str] = Field([], description="要添加的好友关系ID列表")
    remove_friendship_ids: List[str] = Field([], description="要移除的好友关系ID列表")
    
    @validator('add_friendship_ids', 'remove_friendship_ids')
    def validate_friendship_ids(cls, v):
        if not isinstance(v, list):
            raise ValueError('必须是列表类型')
        return v


class GroupMemberResponse(BaseModel):
    """分组成员响应模型"""
    id: str = Field(..., description="关联ID")
    group_id: str = Field(..., description="分组ID")
    friendship_id: str = Field(..., description="好友关系ID")
    role: GroupMemberRole = Field(..., description="在分组中的角色")
    joined_at: datetime = Field(..., description="加入时间")
    invited_by: Optional[str] = Field(None, description="邀请人ID")
    
    # 关联的好友信息
    friendship: Optional[FriendshipResponse] = Field(None, description="好友关系信息")

    class Config:
        from_attributes = True


# 隐私设置模型
class ContactPrivacySettingsBase(BaseModel):
    """联系人隐私设置基础模型"""
    allow_search_by_phone: bool = Field(True, description="允许通过手机号搜索")
    allow_search_by_email: bool = Field(True, description="允许通过邮箱搜索")
    allow_search_by_username: bool = Field(True, description="允许通过用户名搜索")
    auto_accept_from_contacts: bool = Field(False, description="自动接受通讯录好友请求")
    require_verification_message: bool = Field(True, description="要求验证消息")
    show_online_status: bool = Field(True, description="显示在线状态")
    show_last_seen: bool = Field(False, description="显示最后在线时间")
    show_profile_to_friends: bool = Field(True, description="向好友显示详细资料")


class UpdatePrivacySettingsRequest(ContactPrivacySettingsBase):
    """更新隐私设置请求模型"""
    pass


class ContactPrivacyResponse(ContactPrivacySettingsBase):
    """联系人隐私设置响应模型"""
    id: str = Field(..., description="设置ID")
    user_id: str = Field(..., description="用户ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# 标签关联模型
class UpdateFriendTagsRequest(BaseModel):
    """更新好友标签请求模型"""
    tag_ids: List[str] = Field(..., description="标签ID列表")
    
    @validator('tag_ids')
    def validate_tag_ids(cls, v):
        if not isinstance(v, list):
            raise ValueError('必须是列表类型')
        return v


class TagSuggestionResponse(BaseModel):
    """标签推荐响应模型"""
    tag_id: Optional[str] = Field(None, description="现有标签ID（如果是现有标签）")
    name: str = Field(..., description="标签名称")
    color: str = Field(..., description="建议的标签颜色")
    reason: str = Field(..., description="推荐原因")
    confidence: float = Field(..., ge=0, le=1, description="推荐置信度")

    class Config:
        from_attributes = True


# 批量操作模型
class BatchFriendOperations(BaseModel):
    """批量好友操作请求模型"""
    friendship_ids: List[str] = Field(..., description="好友关系ID列表")
    operation: str = Field(..., pattern="^(add_tags|remove_tags|move_to_group|remove_from_group|star|unstar|mute|unmute)$", description="操作类型")
    operation_data: Optional[Dict[str, Any]] = Field(None, description="操作相关数据")
    
    @validator('friendship_ids')
    def validate_friendship_ids(cls, v):
        if not v:
            raise ValueError('好友关系ID列表不能为空')
        return v


class BatchOperationResponse(BaseModel):
    """批量操作响应模型"""
    success_count: int = Field(..., description="成功操作的数量")
    failure_count: int = Field(..., description="失败操作的数量")
    errors: List[str] = Field([], description="错误信息列表")


# 统计分析模型
class ContactAnalyticsResponse(BaseModel):
    """联系人使用统计响应模型"""
    total_friends: int = Field(..., description="好友总数")
    active_friends: int = Field(..., description="活跃好友数")
    total_tags: int = Field(..., description="标签总数")
    total_groups: int = Field(..., description="分组总数")
    interactions_this_week: int = Field(..., description="本周互动次数")
    top_tags: List[Dict[str, Any]] = Field([], description="最常用标签")
    recent_activities: List[Dict[str, Any]] = Field([], description="最近活动")

    class Config:
        from_attributes = True


# 群聊创建模型
class CreateGroupChatRequest(BaseModel):
    """基于分组创建群聊请求模型"""
    title: Optional[str] = Field(None, max_length=100, description="群聊标题")
    include_all_members: bool = Field(True, description="是否包含所有分组成员")
    member_ids: Optional[List[str]] = Field(None, description="指定成员ID列表（如果不包含所有成员）")
    initial_message: Optional[str] = Field(None, max_length=500, description="初始消息")


# 分页响应模型
class PaginatedResponse(BaseModel):
    """分页响应基础模型"""
    items: List[Any] = Field(..., description="数据项列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")

    class Config:
        from_attributes = True


# 特定类型的分页响应
class PaginatedFriendsResponse(PaginatedResponse):
    """分页好友列表响应模型"""
    items: List[FriendshipResponse] = Field(..., description="好友列表")


class PaginatedGroupMembersResponse(PaginatedResponse):
    """分页分组成员响应模型"""
    items: List[GroupMemberResponse] = Field(..., description="分组成员列表")


class PaginatedFriendRequestsResponse(PaginatedResponse):
    """分页好友请求响应模型"""
    items: List[FriendRequestResponse] = Field(..., description="好友请求列表")
