"""
Contact领域转换器
负责领域对象与Schema之间的转换
"""
from typing import List, Optional
from datetime import datetime

from app.db.models.contacts import Friendship, ContactTag, ContactGroup, ContactGroupMember
from app.db.models.user import User
from app.schemas.contacts import (
    FriendshipResponse, ContactTagResponse, ContactGroupResponse,
    GroupMemberResponse, UserSearchResult
)


class ContactConverter:
    """Contact领域转换器"""
    
    @staticmethod
    def to_friendship_response(friendship: Friendship) -> FriendshipResponse:
        """好友关系转响应模型"""
        return FriendshipResponse(
            id=friendship.id,
            user_id=friendship.user_id,
            friend_id=friendship.friend_id,
            friend_name=friendship.friend.name if friendship.friend else None,
            friend_avatar=friendship.friend.avatar if friendship.friend else None,
            nickname=friendship.nickname,
            remark=friendship.remark,
            status=friendship.status,
            is_starred=friendship.is_starred,
            is_muted=friendship.is_muted,
            is_pinned=friendship.is_pinned,
            is_blocked=friendship.is_blocked,
            tags=[ContactConverter.to_contact_tag_response(tag.tag) for tag in friendship.tags] if friendship.tags else [],
            groups=[ContactConverter.to_contact_group_response(member.group) for member in friendship.group_members] if friendship.group_members else [],
            last_interaction_at=friendship.last_interaction_at,
            interaction_count=friendship.interaction_count,
            created_at=friendship.created_at,
            updated_at=friendship.updated_at
        )
    
    @staticmethod
    def to_friendship_list_response(friendships: List[Friendship]) -> List[FriendshipResponse]:
        """好友关系列表转响应模型"""
        return [ContactConverter.to_friendship_response(friendship) for friendship in friendships]
    
    @staticmethod
    def to_contact_tag_response(tag: ContactTag) -> ContactTagResponse:
        """联系人标签转响应模型"""
        return ContactTagResponse(
            id=tag.id,
            user_id=tag.user_id,
            name=tag.name,
            color=tag.color,
            icon=tag.icon,
            description=tag.description,
            category=tag.category,
            display_order=tag.display_order,
            is_visible=tag.is_visible,
            is_system_tag=tag.is_system_tag,
            usage_count=tag.usage_count,
            created_at=tag.created_at,
            updated_at=tag.updated_at
        )
    
    @staticmethod
    def to_contact_tag_list_response(tags: List[ContactTag]) -> List[ContactTagResponse]:
        """联系人标签列表转响应模型"""
        return [ContactConverter.to_contact_tag_response(tag) for tag in tags]
    
    @staticmethod
    def to_contact_group_response(group: ContactGroup, include_members: bool = False) -> ContactGroupResponse:
        """联系人分组转响应模型"""
        response = ContactGroupResponse(
            id=group.id,
            user_id=group.user_id,
            name=group.name,
            description=group.description,
            color=group.color,
            icon=group.icon,
            group_type=group.group_type,
            member_count=group.member_count,
            is_visible=group.is_visible,
            display_order=group.display_order,
            created_at=group.created_at,
            updated_at=group.updated_at
        )
        
        if include_members and group.members:
            response.members = [
                ContactConverter.to_group_member_response(member) for member in group.members
            ]
        
        return response
    
    @staticmethod
    def to_contact_group_list_response(groups: List[ContactGroup], include_members: bool = False) -> List[ContactGroupResponse]:
        """联系人分组列表转响应模型"""
        return [ContactConverter.to_contact_group_response(group, include_members) for group in groups]
    
    @staticmethod
    def to_group_member_response(member: ContactGroupMember) -> GroupMemberResponse:
        """分组成员转响应模型"""
        return GroupMemberResponse(
            id=member.id,
            group_id=member.group_id,
            friendship_id=member.friendship_id,
            friend_name=member.friendship.friend.name if member.friendship and member.friendship.friend else None,
            friend_avatar=member.friendship.friend.avatar if member.friendship and member.friendship.friend else None,
            role=member.role,
            joined_at=member.joined_at
        )
    
    @staticmethod
    def to_group_member_list_response(members: List[ContactGroupMember]) -> List[GroupMemberResponse]:
        """分组成员列表转响应模型"""
        return [ContactConverter.to_group_member_response(member) for member in members]
    
    @staticmethod
    def to_user_search_result(user: User, current_user_id: str) -> UserSearchResult:
        """用户转搜索结果模型"""
        return UserSearchResult(
            id=user.id,
            name=user.name,
            email=user.email,
            avatar=user.avatar,
            phone=user.phone,
            is_friend=ContactConverter._check_is_friend(user, current_user_id),
            mutual_friends_count=ContactConverter._get_mutual_friends_count(user, current_user_id)
        )
    
    @staticmethod
    def to_user_search_list_response(users: List[User], current_user_id: str) -> List[UserSearchResult]:
        """用户列表转搜索结果模型"""
        return [ContactConverter.to_user_search_result(user, current_user_id) for user in users]
    
    @staticmethod
    def _check_is_friend(user: User, current_user_id: str) -> bool:
        """检查是否为好友关系"""
        # 这里需要根据实际的数据库关系来判断
        # 暂时返回False，实际实现时需要查询好友关系表
        return False
    
    @staticmethod
    def _get_mutual_friends_count(user: User, current_user_id: str) -> int:
        """获取共同好友数量"""
        # 这里需要根据实际的数据库关系来计算
        # 暂时返回0，实际实现时需要查询好友关系表
        return 0
