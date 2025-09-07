"""
Contact领域仓储实现 - 基础设施层
负责Contact领域的数据持久化
遵循DDD分层架构的基础设施层职责
"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from app.contacts.infrastructure.db.contacts import Friendship, ContactTag, ContactGroup, ContactGroupMember, FriendshipTag
from app.contacts.domain.interfaces import IContactRepository

logger = logging.getLogger(__name__)


class ContactRepository(IContactRepository):
    """Contact领域仓储实现"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============ 好友关系相关方法 ============
    
    async def get_friendship_by_id(self, friendship_id: str) -> Optional[Friendship]:
        """根据ID获取好友关系"""
        try:
            return self.db.query(Friendship).filter(
                Friendship.id == friendship_id
            ).options(
                joinedload(Friendship.friend),
                joinedload(Friendship.tags).joinedload(FriendshipTag.tag),
                joinedload(Friendship.group_memberships).joinedload(ContactGroupMember.group)
            ).first()
        except Exception as e:
            logger.error(f"获取好友关系失败: {e}")
            return None
    
    async def get_friendships_by_user_id(self, user_id: str) -> List[Friendship]:
        """获取用户的所有好友关系"""
        try:
            logger.debug(f"开始查询用户好友关系: user_id={user_id}")
            
            # 执行查询
            friendships = self.db.query(Friendship).filter(
                Friendship.user_id == user_id
            ).options(
                joinedload(Friendship.friend),
                joinedload(Friendship.tags).joinedload(FriendshipTag.tag),
                joinedload(Friendship.group_memberships).joinedload(ContactGroupMember.group)
            ).all()
            
            logger.info(f"查询到好友关系数量: {len(friendships)}")
            
            # 记录每个好友关系的详细信息
            for i, friendship in enumerate(friendships):
                logger.debug(f"好友关系[{i}]: id={friendship.id}, user_id={friendship.user_id}, friend_id={friendship.friend_id}")
                
                # 检查friend对象
                if friendship.friend:
                    logger.debug(f"  好友对象: id={friendship.friend.id}, username={friendship.friend.username}, email={friendship.friend.email}")
                else:
                    logger.warning(f"  好友关系 {friendship.id} 缺少friend对象，可能关联查询失败")
                
                # 检查tags
                if friendship.tags:
                    logger.debug(f"  标签数量: {len(friendship.tags)}")
                else:
                    logger.debug(f"  无标签")
                
                # 检查group_memberships
                if friendship.group_memberships:
                    logger.debug(f"  分组成员数量: {len(friendship.group_memberships)}")
                else:
                    logger.debug(f"  无分组成员")
            
            return friendships
            
        except Exception as e:
            logger.error(f"获取用户好友关系失败: user_id={user_id}, error={str(e)}", exc_info=True)
            return []
    
    async def save_friendship(self, friendship: Friendship) -> Friendship:
        """保存好友关系"""
        try:
            self.db.add(friendship)
            self.db.commit()
            self.db.refresh(friendship)
            return friendship
        except Exception as e:
            self.db.rollback()
            logger.error(f"保存好友关系失败: {e}")
            raise
    
    async def delete_friendship(self, friendship_id: str) -> bool:
        """删除好友关系"""
        try:
            friendship = self.db.query(Friendship).filter(
                Friendship.id == friendship_id
            ).first()
            
            if friendship:
                self.db.delete(friendship)
                self.db.commit()
                return True
            
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除好友关系失败: {e}")
            return False
    
    # ============ 联系人标签相关方法 ============
    
    async def get_contact_tag_by_id(self, tag_id: str) -> Optional[ContactTag]:
        """根据ID获取联系人标签"""
        try:
            return self.db.query(ContactTag).filter(
                ContactTag.id == tag_id
            ).first()
        except Exception as e:
            logger.error(f"获取联系人标签失败: {e}")
            return None
    
    async def get_contact_tags_by_user_id(self, user_id: str) -> List[ContactTag]:
        """获取用户的所有联系人标签"""
        try:
            return self.db.query(ContactTag).filter(
                ContactTag.user_id == user_id
            ).order_by(ContactTag.display_order.asc(), ContactTag.name.asc()).all()
        except Exception as e:
            logger.error(f"获取用户联系人标签失败: {e}")
            return []
    
    async def save_contact_tag(self, tag: ContactTag) -> ContactTag:
        """保存联系人标签"""
        try:
            self.db.add(tag)
            self.db.commit()
            self.db.refresh(tag)
            return tag
        except Exception as e:
            self.db.rollback()
            logger.error(f"保存联系人标签失败: {e}")
            raise
    
    async def delete_contact_tag(self, tag_id: str) -> bool:
        """删除联系人标签"""
        try:
            tag = self.db.query(ContactTag).filter(
                ContactTag.id == tag_id
            ).first()
            
            if tag:
                self.db.delete(tag)
                self.db.commit()
                return True
            
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除联系人标签失败: {e}")
            return False
    
    # ============ 联系人分组相关方法 ============
    
    async def get_contact_group_by_id(self, group_id: str) -> Optional[ContactGroup]:
        """根据ID获取联系人分组"""
        try:
            return self.db.query(ContactGroup).filter(
                ContactGroup.id == group_id
            ).options(
                joinedload(ContactGroup.members).joinedload(ContactGroupMember.friendship)
            ).first()
        except Exception as e:
            logger.error(f"获取联系人分组失败: {e}")
            return None
    
    async def get_contact_groups_by_user_id(self, user_id: str) -> List[ContactGroup]:
        """获取用户的所有联系人分组"""
        try:
            return self.db.query(ContactGroup).filter(
                ContactGroup.user_id == user_id
            ).options(
                joinedload(ContactGroup.members).joinedload(ContactGroupMember.friendship)
            ).order_by(ContactGroup.display_order.asc(), ContactGroup.name.asc()).all()
        except Exception as e:
            logger.error(f"获取用户联系人分组失败: {e}")
            return []
    
    async def save_contact_group(self, group: ContactGroup) -> ContactGroup:
        """保存联系人分组"""
        try:
            self.db.add(group)
            self.db.commit()
            self.db.refresh(group)
            return group
        except Exception as e:
            self.db.rollback()
            logger.error(f"保存联系人分组失败: {e}")
            raise
    
    async def delete_contact_group(self, group_id: str) -> bool:
        """删除联系人分组"""
        try:
            group = self.db.query(ContactGroup).filter(
                ContactGroup.id == group_id
            ).first()
            
            if group:
                self.db.delete(group)
                self.db.commit()
                return True
            
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除联系人分组失败: {e}")
            return False
    
    # ============ 辅助方法 ============
    
    async def get_friendships_by_tag_id(self, user_id: str, tag_id: str) -> List[Friendship]:
        """根据标签ID获取好友关系"""
        try:
            return self.db.query(Friendship).join(FriendshipTag).filter(
                Friendship.user_id == user_id,
                FriendshipTag.tag_id == tag_id
            ).options(
                joinedload(Friendship.friend),
                joinedload(Friendship.tags).joinedload(FriendshipTag.tag)
            ).all()
        except Exception as e:
            logger.error(f"根据标签获取好友关系失败: {e}")
            return []
    
    async def get_group_members(self, group_id: str) -> List[ContactGroupMember]:
        """获取分组成员"""
        try:
            return self.db.query(ContactGroupMember).filter(
                ContactGroupMember.group_id == group_id
            ).options(
                joinedload(ContactGroupMember.friendship).joinedload(Friendship.friend)
            ).all()
        except Exception as e:
            logger.error(f"获取分组成员失败: {e}")
            return []
    
    async def update_group_member_count(self, group_id: str) -> bool:
        """更新分组成员数量"""
        try:
            member_count = self.db.query(ContactGroupMember).filter(
                ContactGroupMember.group_id == group_id
            ).count()
            
            self.db.query(ContactGroup).filter(
                ContactGroup.id == group_id
            ).update({"member_count": member_count})
            
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新分组成员数量失败: {e}")
            return False
