"""
Contact领域转换器
负责领域对象与Schema之间的转换
"""
import logging
from typing import List

from app.contacts.infrastructure.db.contacts import Friendship, ContactTag, ContactGroup, ContactGroupMember
from app.identity_access.infrastructure.db.user import User
from app.contacts.schemas.contacts import (
    FriendshipResponse, ContactTagResponse, ContactGroupResponse,
    GroupMemberResponse, UserSearchResult
)   

logger = logging.getLogger(__name__)


class ContactConverter:
    """Contact领域转换器"""
    
    @staticmethod
    def to_friendship_response(friendship: Friendship) -> FriendshipResponse:
        """好友关系转响应模型"""
        try:
            logger.debug(f"转换好友关系: friendship_id={friendship.id}, user_id={friendship.user_id}, friend_id={friendship.friend_id}")
            
            # 检查friend对象是否存在
            if friendship.friend:
                logger.debug(f"好友信息: id={friendship.friend.id}, username={friendship.friend.username}, avatar={friendship.friend.avatar}")
            else:
                logger.warning(f"好友关系 {friendship.id} 缺少friend对象")
            
            # 构建好友用户信息字典
            friend_info = None
            if friendship.friend:
                friend_info = {
                    "id": friendship.friend.id,
                    "username": friendship.friend.username,
                    "email": friendship.friend.email,
                    "avatar": friendship.friend.avatar,
                    "phone": friendship.friend.phone
                }
            
            return FriendshipResponse(
                # 基础字段（来自FriendshipBase）
                nickname=friendship.nickname,
                remark=friendship.remark,
                is_starred=friendship.is_starred,
                is_muted=friendship.is_muted,
                is_pinned=friendship.is_pinned,
                
                # 主要字段
                id=friendship.id,
                user_id=friendship.user_id,
                friend_id=friendship.friend_id,
                status=friendship.status,
                source=friendship.source,
                is_blocked=friendship.is_blocked,
                
                # 时间字段
                requested_at=friendship.requested_at,
                accepted_at=friendship.accepted_at,
                last_interaction_at=friendship.last_interaction_at,
                created_at=friendship.created_at,
                updated_at=friendship.updated_at,
                
                # 统计字段
                interaction_count=friendship.interaction_count,
                
                # 关联数据
                friend=friend_info,
                tags=[ContactConverter.to_contact_tag_response(tag.tag) for tag in friendship.tags] if friendship.tags else []
            )
        except Exception as e:
            logger.error(f"转换好友关系失败: friendship_id={friendship.id}, error={str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def to_friendship_list_response(friendships: List[Friendship]) -> List[FriendshipResponse]:
        """好友关系列表转响应模型"""
        logger.debug(f"转换好友关系列表: count={len(friendships)}")
        try:
            return [ContactConverter.to_friendship_response(friendship) for friendship in friendships]
        except Exception as e:
            logger.error(f"转换好友关系列表失败: error={str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def to_contact_tag_response(tag: ContactTag) -> ContactTagResponse:
        """联系人标签转响应模型"""
        try:
            logger.debug(f"转换联系人标签: tag_id={tag.id}, name={tag.name}")
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
        except Exception as e:
            logger.error(f"转换联系人标签失败: tag_id={tag.id}, error={str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def to_contact_tag_list_response(tags: List[ContactTag]) -> List[ContactTagResponse]:
        """联系人标签列表转响应模型"""
        logger.debug(f"转换联系人标签列表: count={len(tags)}")
        try:
            return [ContactConverter.to_contact_tag_response(tag) for tag in tags]
        except Exception as e:
            logger.error(f"转换联系人标签列表失败: error={str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def to_contact_group_response(group: ContactGroup, include_members: bool = False) -> ContactGroupResponse:
        """联系人分组转响应模型"""
        try:
            logger.debug(f"转换联系人分组: group_id={group.id}, name={group.name}, include_members={include_members}")
            
            response = ContactGroupResponse(
                id=group.id,
                user_id=group.user_id,
                name=group.name,
                description=group.description,
                avatar=getattr(group, 'avatar', None),  # 可能不存在的字段
                group_type=getattr(group, 'group_type', 'personal'),  # 可能不存在的字段
                color_theme=getattr(group, 'color_theme', '#3B82F6'),  # 可能不存在的字段
                display_order=getattr(group, 'display_order', 0),  # 可能不存在的字段
                is_collapsed=getattr(group, 'is_collapsed', False),  # 可能不存在的字段
                max_members=getattr(group, 'max_members', None),  # 可能不存在的字段
                is_private=getattr(group, 'is_private', False),  # 可能不存在的字段
                member_count=getattr(group, 'member_count', 0),  # 可能不存在的字段
                created_at=group.created_at,
                updated_at=group.updated_at
            )
            
            if include_members and group.members:
                logger.debug(f"转换分组成员: count={len(group.members)}")
                response.members = [
                    ContactConverter.to_group_member_response(member) for member in group.members
                ]
            
            return response
        except Exception as e:
            logger.error(f"转换联系人分组失败: group_id={group.id}, error={str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def to_contact_group_list_response(groups: List[ContactGroup], include_members: bool = False) -> List[ContactGroupResponse]:
        """联系人分组列表转响应模型"""
        logger.debug(f"转换联系人分组列表: count={len(groups)}, include_members={include_members}")
        try:
            return [ContactConverter.to_contact_group_response(group, include_members) for group in groups]
        except Exception as e:
            logger.error(f"转换联系人分组列表失败: error={str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def to_group_member_response(member: ContactGroupMember) -> GroupMemberResponse:
        """分组成员转响应模型"""
        try:
            logger.debug(f"转换分组成员: member_id={member.id}, group_id={member.group_id}, friendship_id={member.friendship_id}")
            
            # 检查friendship和friend对象
            if member.friendship and member.friendship.friend:
                logger.debug(f"分组成员好友信息: id={member.friendship.friend.id}, username={member.friendship.friend.username}")
            else:
                logger.warning(f"分组成员 {member.id} 缺少friendship或friend对象")
            
            return GroupMemberResponse(
                id=member.id,
                group_id=member.group_id,
                friendship_id=member.friendship_id,
                role=member.role,
                joined_at=member.joined_at,
                invited_by=getattr(member, 'invited_by', None),  # 可能不存在的字段
                friendship=ContactConverter.to_friendship_response(member.friendship) if member.friendship else None
            )
        except Exception as e:
            logger.error(f"转换分组成员失败: member_id={member.id}, error={str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def to_group_member_list_response(members: List[ContactGroupMember]) -> List[GroupMemberResponse]:
        """分组成员列表转响应模型"""
        logger.debug(f"转换分组成员列表: count={len(members)}")
        try:
            return [ContactConverter.to_group_member_response(member) for member in members]
        except Exception as e:
            logger.error(f"转换分组成员列表失败: error={str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def to_user_search_result(user: User, current_user_id: str) -> UserSearchResult:
        """用户转搜索结果模型"""
        try:
            logger.debug(f"转换用户搜索结果: user_id={user.id}, username={user.username}, current_user_id={current_user_id}")
            
            # 检查用户对象属性
            logger.debug(f"用户属性: id={user.id}, username={user.username}, email={user.email}, avatar={user.avatar}, phone={user.phone}")
            
            return UserSearchResult(
                id=user.id,
                name=user.username,  # 修复：使用username而不是name
                email=user.email,
                avatar=user.avatar,
                phone=user.phone,
                is_friend=ContactConverter._check_is_friend(user, current_user_id),
                mutual_friends_count=ContactConverter._get_mutual_friends_count(user, current_user_id)
            )
        except Exception as e:
            logger.error(f"转换用户搜索结果失败: user_id={user.id}, error={str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def to_user_search_list_response(users: List[User], current_user_id: str) -> List[UserSearchResult]:
        """用户列表转搜索结果模型"""
        logger.debug(f"转换用户搜索结果列表: count={len(users)}, current_user_id={current_user_id}")
        try:
            return [ContactConverter.to_user_search_result(user, current_user_id) for user in users]
        except Exception as e:
            logger.error(f"转换用户搜索结果列表失败: error={str(e)}", exc_info=True)
            raise
    
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
