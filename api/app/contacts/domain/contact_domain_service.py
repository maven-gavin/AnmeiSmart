"""
Contact领域服务 - 领域层
负责Contact领域的核心业务逻辑
遵循DDD分层架构的领域层职责
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from app.contacts.schemas.contacts import ContactTagCreate, CreateContactGroupRequest
from app.contacts.domain.interfaces import IContactDomainService, IContactRepository

logger = logging.getLogger(__name__)


class ContactDomainService(IContactDomainService):
    """Contact领域服务 - 实现Contact领域的核心业务逻辑"""
    
    def __init__(self, contact_repository: IContactRepository):
        self.contact_repository = contact_repository
    
    async def verify_friendship_exists(self, user_id: str, friend_id: str) -> bool:
        """验证好友关系是否存在 - 领域逻辑"""
        try:
            # 检查是否存在好友关系
            friendships = await self.contact_repository.get_friendships_by_user_id(user_id)
            
            # 检查是否有与指定用户的好友关系
            for friendship in friendships:
                if friendship.friend_id == friend_id:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"验证好友关系失败: {e}")
            return False
    
    async def create_friendship(self, user_id: str, friend_id: str, **kwargs) -> Any:
        """创建好友关系 - 领域逻辑"""
        try:
            # 领域规则验证
            if user_id == friend_id:
                raise ValueError("不能与自己建立好友关系")
            
            # 检查是否已存在好友关系
            if await self.verify_friendship_exists(user_id, friend_id):
                raise ValueError("好友关系已存在")
            
            # 创建好友关系对象
            from app.contacts.infrastructure.db.contacts import Friendship
            from app.common.infrastructure.db.uuid_utils import friendship_id
            
            friendship = Friendship(
                id=friendship_id(),
                user_id=user_id,
                friend_id=friend_id,
                status=kwargs.get("status", "pending"),
                verification_message=kwargs.get("verification_message"),
                source=kwargs.get("source", "manual"),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            return friendship
            
        except Exception as e:
            logger.error(f"创建好友关系失败: {e}")
            raise
    
    async def update_friendship_status(self, friendship: Any, status: str) -> Any:
        """更新好友关系状态 - 领域逻辑"""
        try:
            # 领域规则验证
            valid_statuses = ["pending", "accepted", "rejected", "blocked", "deleted"]
            if status not in valid_statuses:
                raise ValueError(f"无效的状态值: {status}")
            
            # 更新状态
            friendship.status = status
            friendship.updated_at = datetime.utcnow()
            
            # 如果状态变为accepted，更新最后交互时间
            if status == "accepted":
                friendship.last_interaction_at = datetime.utcnow()
                friendship.interaction_count = 0
            
            return friendship
            
        except Exception as e:
            logger.error(f"更新好友关系状态失败: {e}")
            raise
    
    async def create_contact_tag(self, user_id: str, tag_data: ContactTagCreate) -> Any:
        """创建联系人标签 - 领域逻辑"""
        try:
            # 领域规则验证
            if not tag_data.name or not tag_data.name.strip():
                raise ValueError("标签名称不能为空")
            
            if len(tag_data.name.strip()) > 50:
                raise ValueError("标签名称不能超过50个字符")
            
            # 验证标签名称唯一性
            if not await self.validate_tag_name_unique(user_id, tag_data.name):
                raise ValueError("标签名称已存在")
            
            # 创建标签对象
            from app.contacts.infrastructure.db.contacts import ContactTag
            from app.common.infrastructure.db.uuid_utils import tag_id
            
            tag = ContactTag(
                id=tag_id(),
                user_id=user_id,
                name=tag_data.name.strip(),
                color=tag_data.color,
                icon=tag_data.icon,
                description=tag_data.description,
                category=tag_data.category,
                display_order=tag_data.display_order,
                is_visible=tag_data.is_visible,
                is_system_tag=False,
                usage_count=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            return tag
            
        except Exception as e:
            logger.error(f"创建联系人标签失败: {e}")
            raise
    
    async def validate_tag_name_unique(self, user_id: str, tag_name: str, exclude_id: Optional[str] = None) -> bool:
        """验证标签名称唯一性 - 领域逻辑"""
        try:
            # 获取用户的所有标签
            tags = await self.contact_repository.get_contact_tags_by_user_id(user_id)
            
            # 检查名称是否重复
            for tag in tags:
                if tag.name.lower() == tag_name.lower():
                    if exclude_id and tag.id == exclude_id:
                        continue
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"验证标签名称唯一性失败: {e}")
            return False
    
    async def create_contact_group(self, user_id: str, group_data: CreateContactGroupRequest) -> Any:
        """创建联系人分组 - 领域逻辑"""
        try:
            # 领域规则验证
            if not group_data.name or not group_data.name.strip():
                raise ValueError("分组名称不能为空")
            
            if len(group_data.name.strip()) > 100:
                raise ValueError("分组名称不能超过100个字符")
            
            # 验证分组名称唯一性
            if not await self.validate_group_name_unique(user_id, group_data.name):
                raise ValueError("分组名称已存在")
            
            # 创建分组对象
            from app.contacts.infrastructure.db.contacts import ContactGroup
            from app.common.infrastructure.db.uuid_utils import group_id
            
            group = ContactGroup(
                id=group_id(),
                user_id=user_id,
                name=group_data.name.strip(),
                description=group_data.description,
                color=group_data.color,
                icon=group_data.icon,
                group_type=group_data.group_type,
                member_count=0,
                is_visible=group_data.is_visible,
                display_order=group_data.display_order,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            return group
            
        except Exception as e:
            logger.error(f"创建联系人分组失败: {e}")
            raise
    
    async def validate_group_name_unique(self, user_id: str, group_name: str, exclude_id: Optional[str] = None) -> bool:
        """验证分组名称唯一性 - 领域逻辑"""
        try:
            # 获取用户的所有分组
            groups = await self.contact_repository.get_contact_groups_by_user_id(user_id)
            
            # 检查名称是否重复
            for group in groups:
                if group.name.lower() == group_name.lower():
                    if exclude_id and group.id == exclude_id:
                        continue
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"验证分组名称唯一性失败: {e}")
            return False
    
    async def calculate_contact_analytics(self, user_id: str, period: str) -> Dict[str, Any]:
        """计算联系人统计数据 - 领域逻辑"""
        try:
            # 获取用户的所有好友关系
            friendships = await self.contact_repository.get_friendships_by_user_id(user_id)
            
            # 计算基础统计
            total_friends = len([f for f in friendships if f.status == "accepted"])
            pending_requests = len([f for f in friendships if f.status == "pending"])
            blocked_friends = len([f for f in friendships if f.status == "blocked"])
            
            # 计算活跃好友（最近7天有交互）
            recent_date = datetime.utcnow() - timedelta(days=7)
            active_friends = len([
                f for f in friendships 
                if f.status == "accepted" and f.last_interaction_at and f.last_interaction_at >= recent_date
            ])
            
            # 计算新增好友（根据周期）
            if period == "week":
                start_date = datetime.utcnow() - timedelta(days=7)
            elif period == "month":
                start_date = datetime.utcnow() - timedelta(days=30)
            elif period == "quarter":
                start_date = datetime.utcnow() - timedelta(days=90)
            elif period == "year":
                start_date = datetime.utcnow() - timedelta(days=365)
            else:
                start_date = datetime.utcnow() - timedelta(days=30)
            
            new_friends = len([
                f for f in friendships 
                if f.status == "accepted" and f.created_at >= start_date
            ])
            
            # 计算交互统计
            total_interactions = sum(f.interaction_count or 0 for f in friendships if f.status == "accepted")
            
            return {
                "total_friends": total_friends,
                "pending_requests": pending_requests,
                "blocked_friends": blocked_friends,
                "active_friends": active_friends,
                "new_friends": new_friends,
                "total_interactions": total_interactions,
                "period": period,
                "calculated_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"计算联系人统计失败: {e}")
            return {
                "total_friends": 0,
                "pending_requests": 0,
                "blocked_friends": 0,
                "active_friends": 0,
                "new_friends": 0,
                "total_interactions": 0,
                "period": period,
                "calculated_at": datetime.utcnow()
            }
