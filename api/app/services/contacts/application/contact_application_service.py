"""
Contact应用服务 - 应用层
负责编排Contact相关的用例，整合好友管理、标签管理、分组管理
遵循DDD分层架构的应用层职责
"""
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.schemas.contacts import (
    ContactTagCreate, ContactTagResponse, FriendshipResponse,
    PaginatedFriendsResponse, UserSearchResult, FriendRequestResponse,
    PaginatedFriendRequestsResponse, CreateContactGroupRequest, 
    ContactGroupResponse, ContactPrivacyResponse, ContactAnalyticsResponse,
    UpdateFriendshipRequest, UpdateFriendTagsRequest, UpdateGroupMembersRequest,
    BatchOperationResponse, TagSuggestionResponse, GroupMemberResponse,
    PaginatedGroupMembersResponse
)
from app.services.contacts.domain.interfaces import (
    IContactRepository, IContactApplicationService, IContactDomainService
)
from app.services.contacts.converters.contact_converter import ContactConverter

logger = logging.getLogger(__name__)


class ContactApplicationService(IContactApplicationService):
    """Contact应用服务 - 整合好友管理、标签管理、分组管理"""
    
    def __init__(
        self,
        contact_repository: IContactRepository,
        contact_domain_service: IContactDomainService
    ):
        self.contact_repository = contact_repository
        self.contact_domain_service = contact_domain_service
    
    # ============ 好友管理用例 ============
    
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
        try:
            # 获取用户的所有好友关系
            friendships = await self.contact_repository.get_friendships_by_user_id(user_id)
            
            # 应用筛选条件
            filtered_friendships = await self._apply_friendship_filters(
                friendships, view, tags, groups, search, status
            )
            
            # 应用排序
            sorted_friendships = await self._apply_friendship_sorting(
                filtered_friendships, sort_by, sort_order
            )
            
            # 应用分页
            total = len(sorted_friendships)
            start_idx = (page - 1) * size
            end_idx = start_idx + size
            paged_friendships = sorted_friendships[start_idx:end_idx]
            
            # 转换为响应模型
            friendship_responses = ContactConverter.to_friendship_list_response(paged_friendships)
            
            return PaginatedFriendsResponse(
                items=friendship_responses,
                total=total,
                page=page,
                size=size,
                pages=(total + size - 1) // size
            )
            
        except Exception as e:
            logger.error(f"获取好友列表失败: {e}")
            raise
    
    async def search_users_use_case(
        self,
        current_user_id: str,
        query: str,
        search_type: str = "all",
        limit: int = 20
    ) -> List[UserSearchResult]:
        """搜索用户用例"""
        try:
            # 这里需要调用用户服务来搜索用户
            # 暂时返回空列表，实际实现时需要集成用户搜索功能
            return []
            
        except Exception as e:
            logger.error(f"搜索用户失败: {e}")
            raise
    
    async def send_friend_request_use_case(
        self,
        user_id: str,
        friend_id: str,
        verification_message: Optional[str] = None,
        source: str = "manual"
    ) -> FriendRequestResponse:
        """发送好友请求用例"""
        try:
            # 验证好友关系是否已存在
            if await self.contact_domain_service.verify_friendship_exists(user_id, friend_id):
                raise ValueError("好友关系已存在")
            
            # 创建好友关系（状态为pending）
            friendship = await self.contact_domain_service.create_friendship(
                user_id=user_id,
                friend_id=friend_id,
                status="pending",
                verification_message=verification_message,
                source=source
            )
            
            # 保存到数据库
            saved_friendship = await self.contact_repository.save_friendship(friendship)
            
            # 转换为响应模型
            return FriendRequestResponse(
                id=saved_friendship.id,
                user_id=saved_friendship.user_id,
                friend_id=saved_friendship.friend_id,
                status=saved_friendship.status,
                verification_message=saved_friendship.verification_message,
                source=saved_friendship.source,
                created_at=saved_friendship.created_at
            )
            
        except Exception as e:
            logger.error(f"发送好友请求失败: {e}")
            raise
    
    async def handle_friend_request_use_case(
        self,
        user_id: str,
        request_id: str,
        action: str,
        message: Optional[str] = None
    ) -> None:
        """处理好友请求用例"""
        try:
            # 获取好友请求
            friendship = await self.contact_repository.get_friendship_by_id(request_id)
            if not friendship:
                raise ValueError("好友请求不存在")
            
            # 验证权限
            if friendship.friend_id != user_id:
                raise ValueError("无权处理此好友请求")
            
            # 更新状态
            if action == "accept":
                updated_friendship = await self.contact_domain_service.update_friendship_status(
                    friendship, "accepted"
                )
            elif action == "reject":
                updated_friendship = await self.contact_domain_service.update_friendship_status(
                    friendship, "rejected"
                )
            else:
                raise ValueError("无效的操作")
            
            # 保存更新
            await self.contact_repository.save_friendship(updated_friendship)
            
        except Exception as e:
            logger.error(f"处理好友请求失败: {e}")
            raise
    
    async def update_friendship_use_case(
        self,
        user_id: str,
        friendship_id: str,
        update_data: Dict[str, Any]
    ) -> FriendshipResponse:
        """更新好友关系用例"""
        try:
            # 获取好友关系
            friendship = await self.contact_repository.get_friendship_by_id(friendship_id)
            if not friendship:
                raise ValueError("好友关系不存在")
            
            # 验证权限
            if friendship.user_id != user_id:
                raise ValueError("无权更新此好友关系")
            
            # 应用更新
            for key, value in update_data.items():
                if hasattr(friendship, key):
                    setattr(friendship, key, value)
            
            # 保存更新
            updated_friendship = await self.contact_repository.save_friendship(friendship)
            
            # 转换为响应模型
            return ContactConverter.to_friendship_response(updated_friendship)
            
        except Exception as e:
            logger.error(f"更新好友关系失败: {e}")
            raise
    
    async def delete_friendship_use_case(
        self,
        user_id: str,
        friendship_id: str
    ) -> None:
        """删除好友关系用例"""
        try:
            # 获取好友关系
            friendship = await self.contact_repository.get_friendship_by_id(friendship_id)
            if not friendship:
                raise ValueError("好友关系不存在")
            
            # 验证权限
            if friendship.user_id != user_id:
                raise ValueError("无权删除此好友关系")
            
            # 删除好友关系
            await self.contact_repository.delete_friendship(friendship_id)
            
        except Exception as e:
            logger.error(f"删除好友关系失败: {e}")
            raise
    
    # ============ 标签管理用例 ============
    
    async def get_contact_tags_use_case(
        self,
        user_id: str,
        category: Optional[str] = None,
        include_system: bool = True
    ) -> List[ContactTagResponse]:
        """获取联系人标签用例"""
        try:
            # 获取用户的所有标签
            tags = await self.contact_repository.get_contact_tags_by_user_id(user_id)
            
            # 应用筛选条件
            if category:
                tags = [tag for tag in tags if tag.category == category]
            
            if not include_system:
                tags = [tag for tag in tags if not tag.is_system_tag]
            
            # 转换为响应模型
            return ContactConverter.to_contact_tag_list_response(tags)
            
        except Exception as e:
            logger.error(f"获取联系人标签失败: {e}")
            raise
    
    async def create_contact_tag_use_case(
        self,
        user_id: str,
        tag_data: ContactTagCreate
    ) -> ContactTagResponse:
        """创建联系人标签用例"""
        try:
            # 验证标签名称唯一性
            if not await self.contact_domain_service.validate_tag_name_unique(
                user_id, tag_data.name
            ):
                raise ValueError("标签名称已存在")
            
            # 创建标签
            tag = await self.contact_domain_service.create_contact_tag(user_id, tag_data)
            
            # 保存到数据库
            saved_tag = await self.contact_repository.save_contact_tag(tag)
            
            # 转换为响应模型
            return ContactConverter.to_contact_tag_response(saved_tag)
            
        except Exception as e:
            logger.error(f"创建联系人标签失败: {e}")
            raise
    
    async def update_contact_tag_use_case(
        self,
        user_id: str,
        tag_id: str,
        update_data: Dict[str, Any]
    ) -> ContactTagResponse:
        """更新联系人标签用例"""
        try:
            # 获取标签
            tag = await self.contact_repository.get_contact_tag_by_id(tag_id)
            if not tag:
                raise ValueError("标签不存在")
            
            # 验证权限
            if tag.user_id != user_id:
                raise ValueError("无权更新此标签")
            
            # 验证名称唯一性（如果更新名称）
            if "name" in update_data:
                if not await self.contact_domain_service.validate_tag_name_unique(
                    user_id, update_data["name"], exclude_id=tag_id
                ):
                    raise ValueError("标签名称已存在")
            
            # 应用更新
            for key, value in update_data.items():
                if hasattr(tag, key):
                    setattr(tag, key, value)
            
            # 保存更新
            updated_tag = await self.contact_repository.save_contact_tag(tag)
            
            # 转换为响应模型
            return ContactConverter.to_contact_tag_response(updated_tag)
            
        except Exception as e:
            logger.error(f"更新联系人标签失败: {e}")
            raise
    
    async def delete_contact_tag_use_case(
        self,
        user_id: str,
        tag_id: str
    ) -> None:
        """删除联系人标签用例"""
        try:
            # 获取标签
            tag = await self.contact_repository.get_contact_tag_by_id(tag_id)
            if not tag:
                raise ValueError("标签不存在")
            
            # 验证权限
            if tag.user_id != user_id:
                raise ValueError("无权删除此标签")
            
            # 删除标签
            await self.contact_repository.delete_contact_tag(tag_id)
            
        except Exception as e:
            logger.error(f"删除联系人标签失败: {e}")
            raise
    
    # ============ 分组管理用例 ============
    
    async def get_contact_groups_use_case(
        self,
        user_id: str,
        include_members: bool = False
    ) -> List[ContactGroupResponse]:
        """获取联系人分组用例"""
        try:
            # 获取用户的所有分组
            groups = await self.contact_repository.get_contact_groups_by_user_id(user_id)
            
            # 转换为响应模型
            return ContactConverter.to_contact_group_list_response(groups, include_members)
            
        except Exception as e:
            logger.error(f"获取联系人分组失败: {e}")
            raise
    
    async def create_contact_group_use_case(
        self,
        user_id: str,
        group_data: CreateContactGroupRequest
    ) -> ContactGroupResponse:
        """创建联系人分组用例"""
        try:
            # 验证分组名称唯一性
            if not await self.contact_domain_service.validate_group_name_unique(
                user_id, group_data.name
            ):
                raise ValueError("分组名称已存在")
            
            # 创建分组
            group = await self.contact_domain_service.create_contact_group(user_id, group_data)
            
            # 保存到数据库
            saved_group = await self.contact_repository.save_contact_group(group)
            
            # 转换为响应模型
            return ContactConverter.to_contact_group_response(saved_group)
            
        except Exception as e:
            logger.error(f"创建联系人分组失败: {e}")
            raise
    
    async def update_contact_group_use_case(
        self,
        user_id: str,
        group_id: str,
        update_data: Dict[str, Any]
    ) -> ContactGroupResponse:
        """更新联系人分组用例"""
        try:
            # 获取分组
            group = await self.contact_repository.get_contact_group_by_id(group_id)
            if not group:
                raise ValueError("分组不存在")
            
            # 验证权限
            if group.user_id != user_id:
                raise ValueError("无权更新此分组")
            
            # 验证名称唯一性（如果更新名称）
            if "name" in update_data:
                if not await self.contact_domain_service.validate_group_name_unique(
                    user_id, update_data["name"], exclude_id=group_id
                ):
                    raise ValueError("分组名称已存在")
            
            # 应用更新
            for key, value in update_data.items():
                if hasattr(group, key):
                    setattr(group, key, value)
            
            # 保存更新
            updated_group = await self.contact_repository.save_contact_group(group)
            
            # 转换为响应模型
            return ContactConverter.to_contact_group_response(updated_group)
            
        except Exception as e:
            logger.error(f"更新联系人分组失败: {e}")
            raise
    
    async def delete_contact_group_use_case(
        self,
        user_id: str,
        group_id: str
    ) -> None:
        """删除联系人分组用例"""
        try:
            # 获取分组
            group = await self.contact_repository.get_contact_group_by_id(group_id)
            if not group:
                raise ValueError("分组不存在")
            
            # 验证权限
            if group.user_id != user_id:
                raise ValueError("无权删除此分组")
            
            # 删除分组
            await self.contact_repository.delete_contact_group(group_id)
            
        except Exception as e:
            logger.error(f"删除联系人分组失败: {e}")
            raise
    
    # ============ 统计分析用例 ============
    
    async def get_contact_analytics_use_case(
        self,
        user_id: str,
        period: str = "month"
    ) -> ContactAnalyticsResponse:
        """获取联系人统计用例"""
        try:
            # 计算统计数据
            analytics_data = await self.contact_domain_service.calculate_contact_analytics(
                user_id, period
            )
            
            # 转换为响应模型
            return ContactAnalyticsResponse(**analytics_data)
            
        except Exception as e:
            logger.error(f"获取联系人统计失败: {e}")
            raise
    
    # ============ 私有辅助方法 ============
    
    async def _apply_friendship_filters(
        self,
        friendships: List[Any],
        view: Optional[str] = None,
        tags: Optional[List[str]] = None,
        groups: Optional[List[str]] = None,
        search: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Any]:
        """应用好友关系筛选条件"""
        filtered = friendships
        
        # 视图筛选
        if view == "starred":
            filtered = [f for f in filtered if f.is_starred]
        elif view == "recent":
            # 最近7天有交互的好友
            from datetime import datetime, timedelta
            recent_date = datetime.now() - timedelta(days=7)
            filtered = [f for f in filtered if f.last_interaction_at and f.last_interaction_at >= recent_date]
        elif view == "blocked":
            filtered = [f for f in filtered if f.is_blocked]
        elif view == "pending":
            filtered = [f for f in filtered if f.status == "pending"]
        
        # 状态筛选
        if status:
            filtered = [f for f in filtered if f.status == status]
        
        # 搜索筛选
        if search:
            search_lower = search.lower()
            filtered = [f for f in filtered if (
                (f.friend and f.friend.name and search_lower in f.friend.name.lower()) or
                (f.nickname and search_lower in f.nickname.lower()) or
                (f.remark and search_lower in f.remark.lower())
            )]
        
        return filtered
    
    async def _apply_friendship_sorting(
        self,
        friendships: List[Any],
        sort_by: str = "name",
        sort_order: str = "asc"
    ) -> List[Any]:
        """应用好友关系排序"""
        reverse = sort_order.lower() == "desc"
        
        if sort_by == "name":
            friendships.sort(
                key=lambda f: (f.friend.name if f.friend and f.friend.name else "") or 
                             (f.nickname or ""),
                reverse=reverse
            )
        elif sort_by == "recent":
            friendships.sort(
                key=lambda f: f.last_interaction_at or f.created_at,
                reverse=reverse
            )
        elif sort_by == "added":
            friendships.sort(
                key=lambda f: f.created_at,
                reverse=reverse
            )
        elif sort_by == "interaction":
            friendships.sort(
                key=lambda f: f.interaction_count or 0,
                reverse=reverse
            )
        
        return friendships
