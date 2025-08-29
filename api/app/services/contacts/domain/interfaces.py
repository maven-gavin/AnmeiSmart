"""
Contact领域层接口定义
遵循DDD分层架构的领域层职责
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.schemas.contacts import (
    ContactTagCreate, ContactTagResponse, FriendshipResponse,
    PaginatedFriendsResponse, UserSearchResult, FriendRequestResponse,
    PaginatedFriendRequestsResponse, CreateContactGroupRequest, 
    ContactGroupResponse, ContactPrivacyResponse, ContactAnalyticsResponse,
    UpdateFriendshipRequest, UpdateFriendTagsRequest, UpdateGroupMembersRequest,
    BatchOperationResponse, TagSuggestionResponse, GroupMemberResponse,
    PaginatedGroupMembersResponse
)


class IContactRepository(ABC):
    """联系人仓储抽象接口"""
    
    @abstractmethod
    async def get_friendship_by_id(self, friendship_id: str) -> Optional[Any]:
        """根据ID获取好友关系"""
        pass
    
    @abstractmethod
    async def get_friendships_by_user_id(self, user_id: str) -> List[Any]:
        """获取用户的所有好友关系"""
        pass
    
    @abstractmethod
    async def save_friendship(self, friendship: Any) -> Any:
        """保存好友关系"""
        pass
    
    @abstractmethod
    async def delete_friendship(self, friendship_id: str) -> bool:
        """删除好友关系"""
        pass
    
    @abstractmethod
    async def get_contact_tag_by_id(self, tag_id: str) -> Optional[Any]:
        """根据ID获取联系人标签"""
        pass
    
    @abstractmethod
    async def get_contact_tags_by_user_id(self, user_id: str) -> List[Any]:
        """获取用户的所有联系人标签"""
        pass
    
    @abstractmethod
    async def save_contact_tag(self, tag: Any) -> Any:
        """保存联系人标签"""
        pass
    
    @abstractmethod
    async def delete_contact_tag(self, tag_id: str) -> bool:
        """删除联系人标签"""
        pass
    
    @abstractmethod
    async def get_contact_group_by_id(self, group_id: str) -> Optional[Any]:
        """根据ID获取联系人分组"""
        pass
    
    @abstractmethod
    async def get_contact_groups_by_user_id(self, user_id: str) -> List[Any]:
        """获取用户的所有联系人分组"""
        pass
    
    @abstractmethod
    async def save_contact_group(self, group: Any) -> Any:
        """保存联系人分组"""
        pass
    
    @abstractmethod
    async def delete_contact_group(self, group_id: str) -> bool:
        """删除联系人分组"""
        pass


class IContactApplicationService(ABC):
    """联系人应用服务抽象接口"""
    
    @abstractmethod
    async def get_friends_use_case(
        self,
        user_id: str,
        view: Optional[str] = None,
        tags: Optional[List[str]] = None,
        groups: Optional[List[str]] = None,
        search: Optional[str] = None,
        status: Optional[str] = None,
        sort_by: str = "name",
        sort_order: str = "asc",
        page: int = 1,
        size: int = 20
    ) -> PaginatedFriendsResponse:
        """获取好友列表用例"""
        pass
    
    @abstractmethod
    async def search_users_use_case(
        self,
        current_user_id: str,
        query: str,
        search_type: str = "all",
        limit: int = 20
    ) -> List[UserSearchResult]:
        """搜索用户用例"""
        pass
    
    @abstractmethod
    async def send_friend_request_use_case(
        self,
        user_id: str,
        friend_id: str,
        verification_message: Optional[str] = None,
        source: str = "manual"
    ) -> FriendRequestResponse:
        """发送好友请求用例"""
        pass
    
    @abstractmethod
    async def handle_friend_request_use_case(
        self,
        user_id: str,
        request_id: str,
        action: str,
        message: Optional[str] = None
    ) -> None:
        """处理好友请求用例"""
        pass
    
    @abstractmethod
    async def update_friendship_use_case(
        self,
        user_id: str,
        friendship_id: str,
        update_data: Dict[str, Any]
    ) -> FriendshipResponse:
        """更新好友关系用例"""
        pass
    
    @abstractmethod
    async def delete_friendship_use_case(
        self,
        user_id: str,
        friendship_id: str
    ) -> None:
        """删除好友关系用例"""
        pass
    
    @abstractmethod
    async def get_contact_tags_use_case(
        self,
        user_id: str,
        category: Optional[str] = None,
        include_system: bool = True
    ) -> List[ContactTagResponse]:
        """获取联系人标签用例"""
        pass
    
    @abstractmethod
    async def create_contact_tag_use_case(
        self,
        user_id: str,
        tag_data: ContactTagCreate
    ) -> ContactTagResponse:
        """创建联系人标签用例"""
        pass
    
    @abstractmethod
    async def update_contact_tag_use_case(
        self,
        user_id: str,
        tag_id: str,
        update_data: Dict[str, Any]
    ) -> ContactTagResponse:
        """更新联系人标签用例"""
        pass
    
    @abstractmethod
    async def delete_contact_tag_use_case(
        self,
        user_id: str,
        tag_id: str
    ) -> None:
        """删除联系人标签用例"""
        pass
    
    @abstractmethod
    async def get_contact_groups_use_case(
        self,
        user_id: str,
        include_members: bool = False
    ) -> List[ContactGroupResponse]:
        """获取联系人分组用例"""
        pass
    
    @abstractmethod
    async def create_contact_group_use_case(
        self,
        user_id: str,
        group_data: CreateContactGroupRequest
    ) -> ContactGroupResponse:
        """创建联系人分组用例"""
        pass
    
    @abstractmethod
    async def update_contact_group_use_case(
        self,
        user_id: str,
        group_id: str,
        update_data: Dict[str, Any]
    ) -> ContactGroupResponse:
        """更新联系人分组用例"""
        pass
    
    @abstractmethod
    async def delete_contact_group_use_case(
        self,
        user_id: str,
        group_id: str
    ) -> None:
        """删除联系人分组用例"""
        pass
    
    @abstractmethod
    async def get_contact_analytics_use_case(
        self,
        user_id: str,
        period: str = "month"
    ) -> ContactAnalyticsResponse:
        """获取联系人统计用例"""
        pass


class IContactDomainService(ABC):
    """联系人领域服务抽象接口"""
    
    @abstractmethod
    async def verify_friendship_exists(self, user_id: str, friend_id: str) -> bool:
        """验证好友关系是否存在 - 领域逻辑"""
        pass
    
    @abstractmethod
    async def create_friendship(self, user_id: str, friend_id: str, **kwargs) -> Any:
        """创建好友关系 - 领域逻辑"""
        pass
    
    @abstractmethod
    async def update_friendship_status(self, friendship: Any, status: str) -> Any:
        """更新好友关系状态 - 领域逻辑"""
        pass
    
    @abstractmethod
    async def create_contact_tag(self, user_id: str, tag_data: ContactTagCreate) -> Any:
        """创建联系人标签 - 领域逻辑"""
        pass
    
    @abstractmethod
    async def validate_tag_name_unique(self, user_id: str, tag_name: str, exclude_id: Optional[str] = None) -> bool:
        """验证标签名称唯一性 - 领域逻辑"""
        pass
    
    @abstractmethod
    async def create_contact_group(self, user_id: str, group_data: CreateContactGroupRequest) -> Any:
        """创建联系人分组 - 领域逻辑"""
        pass
    
    @abstractmethod
    async def validate_group_name_unique(self, user_id: str, group_name: str, exclude_id: Optional[str] = None) -> bool:
        """验证分组名称唯一性 - 领域逻辑"""
        pass
    
    @abstractmethod
    async def calculate_contact_analytics(self, user_id: str, period: str) -> Dict[str, Any]:
        """计算联系人统计数据 - 领域逻辑"""
        pass
