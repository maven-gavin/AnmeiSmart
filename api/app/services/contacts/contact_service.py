"""
通讯录核心服务类
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func, text
from datetime import datetime, timedelta
import logging

from app.db.models.contacts import (
    Friendship, ContactTag, FriendshipTag, ContactGroup, 
    ContactGroupMember, ContactPrivacySetting, InteractionRecord
)
from app.db.models.user import User
from app.schemas.contacts import (
    ContactTagCreate, ContactTagResponse, FriendshipResponse,
    PaginatedFriendsResponse, UserSearchResult, FriendRequestResponse,
    PaginatedFriendRequestsResponse, CreateContactGroupRequest, 
    ContactGroupResponse, ContactPrivacyResponse, ContactAnalyticsResponse
)
from app.db.uuid_utils import friendship_id, tag_id, group_id, setting_id, record_id

logger = logging.getLogger(__name__)


class ContactService:
    """通讯录核心服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============================================================================
    # 好友管理相关方法
    # ============================================================================
    
    async def get_friends(
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
        """获取好友列表"""
        try:
            # 构建基础查询
            query = self.db.query(Friendship).filter(
                Friendship.user_id == user_id
            ).options(
                joinedload(Friendship.friend),
                joinedload(Friendship.tags).joinedload(FriendshipTag.tag)
            )
            
            # 应用筛选条件
            if view == "starred":
                query = query.filter(Friendship.is_starred == True)
            elif view == "recent":
                query = query.filter(
                    Friendship.last_interaction_at >= datetime.now() - timedelta(days=7)
                )
            elif view == "blocked":
                query = query.filter(Friendship.is_blocked == True)
            elif view == "pending":
                query = query.filter(Friendship.status == "pending")
            else:
                # 默认只显示已接受的好友
                query = query.filter(Friendship.status == "accepted")
            
            # 状态筛选
            if status:
                query = query.filter(Friendship.status == status)
            
            # 标签筛选
            if tags:
                query = query.join(FriendshipTag).filter(
                    FriendshipTag.tag_id.in_(tags)
                )
            
            # 搜索功能
            if search:
                search_term = f"%{search}%"
                query = query.join(User, Friendship.friend_id == User.id).filter(
                    or_(
                        User.username.ilike(search_term),
                        Friendship.nickname.ilike(search_term),
                        Friendship.remark.ilike(search_term)
                    )
                )
            
            # 排序
            if sort_by == "name":
                if sort_order == "desc":
                    query = query.join(User, Friendship.friend_id == User.id).order_by(desc(User.username))
                else:
                    query = query.join(User, Friendship.friend_id == User.id).order_by(asc(User.username))
            elif sort_by == "recent":
                query = query.order_by(desc(Friendship.last_interaction_at))
            elif sort_by == "added":
                query = query.order_by(desc(Friendship.created_at))
            elif sort_by == "interaction":
                query = query.order_by(desc(Friendship.interaction_count))
            
            # 分页
            total = query.count()
            friendships = query.offset((page - 1) * size).limit(size).all()
            
            # 转换为响应模型
            items = []
            for friendship in friendships:
                friend_data = {
                    "id": friendship.friend.id,
                    "username": friendship.friend.username,
                    "avatar": friendship.friend.avatar,
                    "roles": [role.name for role in friendship.friend.roles] if friendship.friend.roles else []
                }
                
                tag_data = [
                    ContactTagResponse.from_orm(ft.tag) for ft in friendship.tags
                ]
                
                friendship_response = FriendshipResponse(
                    id=friendship.id,
                    user_id=friendship.user_id,
                    friend_id=friendship.friend_id,
                    status=friendship.status,
                    nickname=friendship.nickname,
                    remark=friendship.remark,
                    source=friendship.source,
                    is_starred=friendship.is_starred,
                    is_muted=friendship.is_muted,
                    is_pinned=friendship.is_pinned,
                    is_blocked=friendship.is_blocked,
                    requested_at=friendship.requested_at,
                    accepted_at=friendship.accepted_at,
                    last_interaction_at=friendship.last_interaction_at,
                    interaction_count=friendship.interaction_count,
                    created_at=friendship.created_at,
                    updated_at=friendship.updated_at,
                    friend=friend_data,
                    tags=tag_data
                )
                items.append(friendship_response)
            
            # 计算分页信息
            pages = (total + size - 1) // size
            
            return PaginatedFriendsResponse(
                items=items,
                total=total,
                page=page,
                size=size,
                pages=pages,
                has_next=page < pages,
                has_prev=page > 1
            )
            
        except Exception as e:
            logger.error(f"获取好友列表失败: {e}")
            raise
    
    async def search_users(
        self,
        current_user_id: str,
        query: str,
        search_type: str = "all",
        limit: int = 10
    ) -> List[UserSearchResult]:
        """搜索用户"""
        try:
            # 构建搜索查询
            search_query = self.db.query(User).options(joinedload(User.roles))
            
            # 排除当前用户
            search_query = search_query.filter(User.id != current_user_id)
            
            # 根据搜索类型构建条件
            search_term = f"%{query}%"
            
            if search_type == "phone":
                search_query = search_query.filter(User.phone.ilike(search_term))
            elif search_type == "email":
                search_query = search_query.filter(User.email.ilike(search_term))
            elif search_type == "username":
                search_query = search_query.filter(User.username.ilike(search_term))
            else:  # all
                search_query = search_query.filter(
                    or_(
                        User.username.ilike(search_term),
                        User.email.ilike(search_term),
                        User.phone.ilike(search_term)
                    )
                )
            
            users = search_query.limit(limit).all()
            
            # 检查与当前用户的好友关系
            user_ids = [user.id for user in users]
            friendships = self.db.query(Friendship).filter(
                Friendship.user_id == current_user_id,
                Friendship.friend_id.in_(user_ids)
            ).all()
            
            friendship_map = {f.friend_id: f for f in friendships}
            
            # 构建响应
            results = []
            for user in users:
                friendship = friendship_map.get(user.id)
                
                result = UserSearchResult(
                    id=user.id,
                    username=user.username,
                    avatar=user.avatar,
                    roles=[role.name for role in user.roles] if user.roles else [],
                    is_friend=friendship is not None,
                    friendship_status=friendship.status if friendship else None
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"搜索用户失败: {e}")
            raise
    
    async def send_friend_request(
        self,
        user_id: str,
        friend_id: str,
        verification_message: Optional[str] = None,
        source: Optional[str] = None
    ) -> FriendRequestResponse:
        """发送好友请求"""
        try:
            # 检查是否已经是好友或已发送请求
            existing = self.db.query(Friendship).filter(
                Friendship.user_id == user_id,
                Friendship.friend_id == friend_id
            ).first()
            
            if existing:
                if existing.status == "accepted":
                    raise ValueError("已经是好友关系")
                elif existing.status == "pending":
                    raise ValueError("已发送好友请求，请等待对方回应")
                elif existing.status == "blocked":
                    raise ValueError("无法添加该用户为好友")
            
            # 检查目标用户是否存在
            friend = self.db.query(User).filter(User.id == friend_id).first()
            if not friend:
                raise ValueError("用户不存在")
            
            # 创建好友请求
            friendship = Friendship(
                id=friendship_id(),
                user_id=user_id,
                friend_id=friend_id,
                status="pending",
                source=source,
                requested_at=datetime.now()
            )
            
            self.db.add(friendship)
            self.db.commit()
            self.db.refresh(friendship)
            
            # 返回请求信息
            user = self.db.query(User).filter(User.id == user_id).first()
            
            return FriendRequestResponse(
                id=friendship.id,
                user_id=friendship.user_id,
                friend_id=friendship.friend_id,
                status=friendship.status,
                verification_message=verification_message,
                source=friendship.source,
                requested_at=friendship.requested_at,
                user={
                    "id": user.id,
                    "username": user.username,
                    "avatar": user.avatar
                },
                friend={
                    "id": friend.id,
                    "username": friend.username,
                    "avatar": friend.avatar
                }
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"发送好友请求失败: {e}")
            raise
    
    # ============================================================================
    # 标签管理相关方法 (简化实现)
    # ============================================================================
    
    async def get_contact_tags(
        self,
        user_id: str,
        category: Optional[str] = None,
        include_system: bool = True
    ) -> List[ContactTagResponse]:
        """获取联系人标签"""
        try:
            query = self.db.query(ContactTag).filter(ContactTag.user_id == user_id)
            
            if category:
                query = query.filter(ContactTag.category == category)
            
            if not include_system:
                query = query.filter(ContactTag.is_system_tag == False)
            
            tags = query.order_by(ContactTag.display_order, ContactTag.name).all()
            
            return [ContactTagResponse.from_orm(tag) for tag in tags]
            
        except Exception as e:
            logger.error(f"获取标签失败: {e}")
            raise
    
    async def create_contact_tag(
        self,
        user_id: str,
        tag_data: ContactTagCreate
    ) -> ContactTagResponse:
        """创建联系人标签"""
        try:
            # 检查名称是否已存在
            existing = self.db.query(ContactTag).filter(
                ContactTag.user_id == user_id,
                ContactTag.name == tag_data.name
            ).first()
            
            if existing:
                raise ValueError("标签名称已存在")
            
            # 创建标签
            tag = ContactTag(
                id=tag_id(),
                user_id=user_id,
                name=tag_data.name,
                color=tag_data.color,
                icon=tag_data.icon,
                description=tag_data.description,
                category=tag_data.category,
                display_order=tag_data.display_order,
                is_visible=tag_data.is_visible,
                is_system_tag=False
            )
            
            self.db.add(tag)
            self.db.commit()
            self.db.refresh(tag)
            
            return ContactTagResponse.from_orm(tag)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建标签失败: {e}")
            raise
    
    # ============================================================================
    # 其他方法的占位符实现
    # ============================================================================
    
    async def get_friend_requests(
        self, 
        user_id: str, 
        request_type: str, 
        status: Optional[str], 
        page: int, 
        size: int
    ) -> PaginatedFriendRequestsResponse:
        """获取好友请求"""
        try:
            # 构建查询
            query = self.db.query(Friendship).options(
                joinedload(Friendship.user),
                joinedload(Friendship.friend)
            )
            
            if request_type == "sent":
                # 我发送的好友请求
                query = query.filter(Friendship.user_id == user_id)
            else:
                # 我接收的好友请求
                query = query.filter(Friendship.friend_id == user_id)
            
            # 状态筛选
            if status:
                query = query.filter(Friendship.status == status)
            else:
                # 默认只显示待处理的请求
                query = query.filter(Friendship.status == "pending")
            
            # 按请求时间倒序
            query = query.order_by(desc(Friendship.requested_at))
            
            # 分页
            total = query.count()
            requests = query.offset((page - 1) * size).limit(size).all()
            
            # 转换为响应模型
            items = []
            for friendship in requests:
                user_data = {
                    "id": friendship.user.id,
                    "username": friendship.user.username,
                    "avatar": friendship.user.avatar
                } if friendship.user else None
                
                friend_data = {
                    "id": friendship.friend.id,
                    "username": friendship.friend.username,
                    "avatar": friendship.friend.avatar
                } if friendship.friend else None
                
                request_response = FriendRequestResponse(
                    id=friendship.id,
                    user_id=friendship.user_id,
                    friend_id=friendship.friend_id,
                    status=friendship.status,
                    verification_message=friendship.remark,  # 使用remark存储验证消息
                    source=friendship.source,
                    requested_at=friendship.requested_at,
                    user=user_data,
                    friend=friend_data
                )
                items.append(request_response)
            
            # 计算分页信息
            pages = (total + size - 1) // size
            
            return PaginatedFriendRequestsResponse(
                items=items,
                total=total,
                page=page,
                size=size,
                pages=pages,
                has_next=page < pages,
                has_prev=page > 1
            )
            
        except Exception as e:
            logger.error(f"获取好友请求失败: {e}")
            raise
    
    async def handle_friend_request(self, user_id: str, request_id: str, action: str, message: Optional[str]):
        """处理好友请求"""
        try:
            # 查找好友请求
            friendship = self.db.query(Friendship).filter(
                Friendship.id == request_id,
                Friendship.friend_id == user_id,  # 确保是发给当前用户的请求
                Friendship.status == "pending"
            ).first()
            
            if not friendship:
                raise ValueError("好友请求不存在或已处理")
            
            if action == "accept":
                # 接受好友请求
                friendship.status = "accepted"
                friendship.accepted_at = datetime.now()
                
                # 创建反向好友关系（双向好友）
                reverse_friendship = Friendship(
                    id=friendship_id(),
                    user_id=user_id,
                    friend_id=friendship.user_id,
                    status="accepted",
                    source="friend_request_accepted",
                    requested_at=friendship.requested_at,
                    accepted_at=datetime.now()
                )
                self.db.add(reverse_friendship)
                
                # 记录互动
                interaction = InteractionRecord(
                    id=record_id(),
                    friendship_id=friendship.id,
                    interaction_type="friend_request_accepted",
                    occurred_at=datetime.now()
                )
                self.db.add(interaction)
                
                logger.info(f"好友请求已接受: {friendship.user_id} -> {user_id}")
                
            elif action == "reject":
                # 拒绝好友请求
                friendship.status = "deleted"  # 标记为已删除
                
                logger.info(f"好友请求已拒绝: {friendship.user_id} -> {user_id}")
            
            else:
                raise ValueError("无效的操作类型")
            
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"处理好友请求失败: {e}")
            raise
    
    async def update_friendship(self, user_id: str, friendship_id: str, update_data: Dict[str, Any]) -> FriendshipResponse:
        """更新好友关系"""
        try:
            # 查找好友关系
            friendship = self.db.query(Friendship).options(
                joinedload(Friendship.friend),
                joinedload(Friendship.tags).joinedload(FriendshipTag.tag)
            ).filter(
                Friendship.id == friendship_id,
                Friendship.user_id == user_id,
                Friendship.status == "accepted"
            ).first()
            
            if not friendship:
                raise ValueError("好友关系不存在")
            
            # 更新字段
            for field, value in update_data.items():
                if hasattr(friendship, field):
                    setattr(friendship, field, value)
            
            # 更新时间戳
            friendship.updated_at = datetime.now()
            
            self.db.commit()
            self.db.refresh(friendship)
            
            # 如果更新了重要设置，记录互动
            if any(key in update_data for key in ['is_starred', 'is_pinned', 'nickname']):
                interaction = InteractionRecord(
                    id=record_id(),
                    friendship_id=friendship.id,
                    interaction_type="profile_updated",
                    interaction_data=update_data,
                    occurred_at=datetime.now()
                )
                self.db.add(interaction)
                self.db.commit()
            
            # 构建响应
            friend_data = {
                "id": friendship.friend.id,
                "username": friendship.friend.username,
                "avatar": friendship.friend.avatar,
                "roles": [role.name for role in friendship.friend.roles] if friendship.friend.roles else []
            }
            
            tag_data = [
                ContactTagResponse.from_orm(ft.tag) for ft in friendship.tags
            ]
            
            return FriendshipResponse(
                id=friendship.id,
                user_id=friendship.user_id,
                friend_id=friendship.friend_id,
                status=friendship.status,
                nickname=friendship.nickname,
                remark=friendship.remark,
                source=friendship.source,
                is_starred=friendship.is_starred,
                is_muted=friendship.is_muted,
                is_pinned=friendship.is_pinned,
                is_blocked=friendship.is_blocked,
                requested_at=friendship.requested_at,
                accepted_at=friendship.accepted_at,
                last_interaction_at=friendship.last_interaction_at,
                interaction_count=friendship.interaction_count,
                created_at=friendship.created_at,
                updated_at=friendship.updated_at,
                friend=friend_data,
                tags=tag_data
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新好友关系失败: {e}")
            raise
    
    async def delete_friendship(self, user_id: str, friendship_id: str):
        """删除好友关系"""
        try:
            # 查找好友关系
            friendship = self.db.query(Friendship).filter(
                Friendship.id == friendship_id,
                Friendship.user_id == user_id
            ).first()
            
            if not friendship:
                raise ValueError("好友关系不存在")
            
            friend_id = friendship.friend_id
            
            # 删除双向好友关系
            # 删除当前用户到好友的关系
            self.db.delete(friendship)
            
            # 查找并删除反向关系
            reverse_friendship = self.db.query(Friendship).filter(
                Friendship.user_id == friend_id,
                Friendship.friend_id == user_id
            ).first()
            
            if reverse_friendship:
                self.db.delete(reverse_friendship)
            
            self.db.commit()
            
            logger.info(f"好友关系已删除: {user_id} <-> {friend_id}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除好友关系失败: {e}")
            raise
    
    async def batch_friend_operations(self, user_id: str, friendship_ids: List[str], operation: str, operation_data: Optional[Dict[str, Any]]):
        """批量好友操作 - 占位符实现"""
        # TODO: 实现完整的批量操作逻辑
        pass
    
    async def update_contact_tag(self, user_id: str, tag_id: str, update_data: Dict[str, Any]) -> ContactTagResponse:
        """更新联系人标签"""
        try:
            # 查找标签
            tag = self.db.query(ContactTag).filter(
                ContactTag.id == tag_id,
                ContactTag.user_id == user_id,
                ContactTag.is_system_tag == False  # 只能更新自定义标签
            ).first()
            
            if not tag:
                raise ValueError("标签不存在或无权限修改")
            
            # 检查名称冲突
            if "name" in update_data:
                existing = self.db.query(ContactTag).filter(
                    ContactTag.user_id == user_id,
                    ContactTag.name == update_data["name"],
                    ContactTag.id != tag_id
                ).first()
                
                if existing:
                    raise ValueError("标签名称已存在")
            
            # 更新字段
            for field, value in update_data.items():
                if hasattr(tag, field):
                    setattr(tag, field, value)
            
            tag.updated_at = datetime.now()
            
            self.db.commit()
            self.db.refresh(tag)
            
            return ContactTagResponse.from_orm(tag)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新标签失败: {e}")
            raise
    
    async def delete_contact_tag(self, user_id: str, tag_id: str):
        """删除联系人标签"""
        try:
            # 查找标签
            tag = self.db.query(ContactTag).filter(
                ContactTag.id == tag_id,
                ContactTag.user_id == user_id,
                ContactTag.is_system_tag == False  # 只能删除自定义标签
            ).first()
            
            if not tag:
                raise ValueError("标签不存在或无权限删除")
            
            # 检查是否有好友使用此标签
            usage_count = self.db.query(FriendshipTag).filter(
                FriendshipTag.tag_id == tag_id
            ).count()
            
            if usage_count > 0:
                # 先删除所有使用此标签的关联关系
                self.db.query(FriendshipTag).filter(
                    FriendshipTag.tag_id == tag_id
                ).delete()
            
            # 删除标签
            self.db.delete(tag)
            self.db.commit()
            
            logger.info(f"标签已删除: {tag.name} (用户: {user_id})")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除标签失败: {e}")
            raise
    
    async def update_friend_tags(self, user_id: str, friendship_id: str, tag_ids: List[str]):
        """更新好友标签"""
        try:
            # 验证好友关系
            friendship = self.db.query(Friendship).filter(
                Friendship.id == friendship_id,
                Friendship.user_id == user_id,
                Friendship.status == "accepted"
            ).first()
            
            if not friendship:
                raise ValueError("好友关系不存在")
            
            # 验证标签是否属于当前用户
            if tag_ids:
                valid_tags = self.db.query(ContactTag).filter(
                    ContactTag.id.in_(tag_ids),
                    ContactTag.user_id == user_id
                ).all()
                
                if len(valid_tags) != len(tag_ids):
                    raise ValueError("包含无效的标签ID")
            
            # 删除现有的标签关联
            self.db.query(FriendshipTag).filter(
                FriendshipTag.friendship_id == friendship_id
            ).delete()
            
            # 创建新的标签关联
            for tag_id in tag_ids:
                friendship_tag = FriendshipTag(
                    id=relation_id(),
                    friendship_id=friendship_id,
                    tag_id=tag_id,
                    assigned_by=user_id,
                    assigned_at=datetime.now()
                )
                self.db.add(friendship_tag)
            
            # 更新标签使用次数
            for tag_id in tag_ids:
                tag = self.db.query(ContactTag).filter(ContactTag.id == tag_id).first()
                if tag:
                    tag.usage_count = self.db.query(FriendshipTag).filter(
                        FriendshipTag.tag_id == tag_id
                    ).count()
            
            # 记录互动
            if tag_ids:
                interaction = InteractionRecord(
                    id=record_id(),
                    friendship_id=friendship_id,
                    interaction_type="tag_added",
                    interaction_data={"tag_ids": tag_ids},
                    occurred_at=datetime.now()
                )
                self.db.add(interaction)
            
            self.db.commit()
            
            logger.info(f"好友标签已更新: friendship={friendship_id}, tags={tag_ids}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新好友标签失败: {e}")
            raise
    
    async def get_friends_by_tag(self, user_id: str, tag_id: str, page: int, size: int) -> PaginatedFriendsResponse:
        """获取指定标签的好友"""
        try:
            # 验证标签是否属于当前用户
            tag = self.db.query(ContactTag).filter(
                ContactTag.id == tag_id,
                ContactTag.user_id == user_id
            ).first()
            
            if not tag:
                raise ValueError("标签不存在")
            
            # 查询拥有此标签的好友
            query = self.db.query(Friendship).options(
                joinedload(Friendship.friend),
                joinedload(Friendship.tags).joinedload(FriendshipTag.tag)
            ).join(FriendshipTag).filter(
                Friendship.user_id == user_id,
                Friendship.status == "accepted",
                FriendshipTag.tag_id == tag_id
            ).order_by(Friendship.last_interaction_at.desc())
            
            # 分页
            total = query.count()
            friendships = query.offset((page - 1) * size).limit(size).all()
            
            # 转换为响应模型
            items = []
            for friendship in friendships:
                friend_data = {
                    "id": friendship.friend.id,
                    "username": friendship.friend.username,
                    "avatar": friendship.friend.avatar,
                    "roles": [role.name for role in friendship.friend.roles] if friendship.friend.roles else []
                }
                
                tag_data = [
                    ContactTagResponse.from_orm(ft.tag) for ft in friendship.tags
                ]
                
                friendship_response = FriendshipResponse(
                    id=friendship.id,
                    user_id=friendship.user_id,
                    friend_id=friendship.friend_id,
                    status=friendship.status,
                    nickname=friendship.nickname,
                    remark=friendship.remark,
                    source=friendship.source,
                    is_starred=friendship.is_starred,
                    is_muted=friendship.is_muted,
                    is_pinned=friendship.is_pinned,
                    is_blocked=friendship.is_blocked,
                    requested_at=friendship.requested_at,
                    accepted_at=friendship.accepted_at,
                    last_interaction_at=friendship.last_interaction_at,
                    interaction_count=friendship.interaction_count,
                    created_at=friendship.created_at,
                    updated_at=friendship.updated_at,
                    friend=friend_data,
                    tags=tag_data
                )
                items.append(friendship_response)
            
            # 计算分页信息
            pages = (total + size - 1) // size
            
            return PaginatedFriendsResponse(
                items=items,
                total=total,
                page=page,
                size=size,
                pages=pages,
                has_next=page < pages,
                has_prev=page > 1
            )
            
        except Exception as e:
            logger.error(f"获取标签好友失败: {e}")
            raise
    
    async def get_tag_suggestions(self, user_id: str, friendship_id: Optional[str]) -> List[Dict[str, Any]]:
        """获取智能标签推荐"""
        try:
            suggestions = []
            
            if friendship_id:
                # 为特定好友推荐标签
                friendship = self.db.query(Friendship).options(
                    joinedload(Friendship.friend).joinedload(User.roles)
                ).filter(
                    Friendship.id == friendship_id,
                    Friendship.user_id == user_id
                ).first()
                
                if friendship and friendship.friend:
                    # 基于好友角色推荐标签
                    friend_roles = [role.name for role in friendship.friend.roles] if friendship.friend.roles else []
                    
                    # 获取用户的标签
                    user_tags = self.db.query(ContactTag).filter(
                        ContactTag.user_id == user_id
                    ).all()
                    
                    tag_map = {tag.name: tag for tag in user_tags}
                    
                    # 基于角色的标签推荐
                    role_tag_mapping = {
                        "doctor": ["医生", "专家", "同行"],
                        "consultant": ["顾问", "同事", "合作伙伴"],
                        "customer": ["客户", "VIP客户", "潜在客户"],
                        "admin": ["上级", "管理层"],
                        "operator": ["同事", "运营"]
                    }
                    
                    for role in friend_roles:
                        if role in role_tag_mapping:
                            for tag_name in role_tag_mapping[role]:
                                if tag_name in tag_map:
                                    tag = tag_map[tag_name]
                                    suggestions.append({
                                        "tag_id": tag.id,
                                        "name": tag.name,
                                        "color": tag.color,
                                        "reason": f"基于好友角色 '{role}' 的推荐",
                                        "confidence": 0.8
                                    })
            
            else:
                # 通用标签推荐，基于用户最常用的标签
                popular_tags = self.db.query(ContactTag).filter(
                    ContactTag.user_id == user_id,
                    ContactTag.usage_count > 0
                ).order_by(desc(ContactTag.usage_count)).limit(5).all()
                
                for tag in popular_tags:
                    suggestions.append({
                        "tag_id": tag.id,
                        "name": tag.name,
                        "color": tag.color,
                        "reason": f"您经常使用的标签（使用了{tag.usage_count}次）",
                        "confidence": min(0.9, tag.usage_count / 10)
                    })
            
            return suggestions[:10]  # 最多返回10个推荐
            
        except Exception as e:
            logger.error(f"获取标签推荐失败: {e}")
            return []
    
    async def get_contact_groups(self, user_id: str, include_members: bool) -> List[ContactGroupResponse]:
        """获取联系人分组"""
        try:
            query = self.db.query(ContactGroup).filter(
                ContactGroup.user_id == user_id
            ).order_by(ContactGroup.display_order, ContactGroup.name)
            
            if include_members:
                query = query.options(
                    joinedload(ContactGroup.members).joinedload(ContactGroupMember.friendship)
                )
            
            groups = query.all()
            
            # 转换为响应模型
            result = []
            for group in groups:
                group_data = ContactGroupResponse(
                    id=group.id,
                    user_id=group.user_id,
                    name=group.name,
                    description=group.description,
                    avatar=group.avatar,
                    group_type=group.group_type,
                    color_theme=group.color_theme,
                    display_order=group.display_order,
                    is_collapsed=group.is_collapsed,
                    max_members=group.max_members,
                    is_private=group.is_private,
                    member_count=group.member_count,
                    created_at=group.created_at,
                    updated_at=group.updated_at
                )
                
                if include_members and group.members:
                    # 添加成员信息
                    members_data = []
                    for member in group.members:
                        if member.friendship:
                            member_data = {
                                "id": member.id,
                                "group_id": member.group_id,
                                "friendship_id": member.friendship_id,
                                "role": member.role,
                                "joined_at": member.joined_at,
                                "friendship": {
                                    "id": member.friendship.id,
                                    "friend_id": member.friendship.friend_id,
                                    "nickname": member.friendship.nickname,
                                    "is_starred": member.friendship.is_starred
                                }
                            }
                            members_data.append(member_data)
                    
                    group_data.members = members_data
                
                result.append(group_data)
            
            return result
            
        except Exception as e:
            logger.error(f"获取分组列表失败: {e}")
            raise
    
    async def create_contact_group(self, user_id: str, group_data):
        """创建联系人分组 - 占位符实现"""
        # TODO: 实现完整的分组创建逻辑
        pass
    
    async def update_contact_group(self, user_id: str, group_id: str, update_data: Dict[str, Any]):
        """更新联系人分组 - 占位符实现"""
        # TODO: 实现完整的分组更新逻辑
        pass
    
    async def delete_contact_group(self, user_id: str, group_id: str):
        """删除联系人分组 - 占位符实现"""
        # TODO: 实现完整的分组删除逻辑
        pass
    
    async def get_group_members(self, user_id: str, group_id: str, page: int, size: int):
        """获取分组成员 - 占位符实现"""
        # TODO: 实现完整的分组成员获取逻辑
        pass
    
    async def update_group_members(self, user_id: str, group_id: str, add_friendship_ids: List[str], remove_friendship_ids: List[str]):
        """更新分组成员 - 占位符实现"""
        # TODO: 实现完整的分组成员更新逻辑
        pass
    
    async def create_group_chat(self, user_id: str, group_id: str, title: Optional[str], include_all_members: bool, member_ids: Optional[List[str]], initial_message: Optional[str]):
        """创建群聊 - 占位符实现"""
        # TODO: 实现完整的群聊创建逻辑
        pass
    
    async def get_privacy_settings(self, user_id: str) -> ContactPrivacyResponse:
        """获取隐私设置"""
        try:
            # 查找用户的隐私设置
            privacy_setting = self.db.query(ContactPrivacySetting).filter(
                ContactPrivacySetting.user_id == user_id
            ).first()
            
            # 如果不存在，创建默认设置
            if not privacy_setting:
                privacy_setting = ContactPrivacySetting(
                    id=setting_id(),
                    user_id=user_id,
                    allow_search_by_phone=True,
                    allow_search_by_email=True,
                    allow_search_by_username=True,
                    auto_accept_from_contacts=False,
                    require_verification_message=True,
                    show_online_status=True,
                    show_last_seen=False,
                    show_profile_to_friends=True
                )
                
                self.db.add(privacy_setting)
                self.db.commit()
                self.db.refresh(privacy_setting)
            
            return ContactPrivacyResponse(
                id=privacy_setting.id,
                user_id=privacy_setting.user_id,
                allow_search_by_phone=privacy_setting.allow_search_by_phone,
                allow_search_by_email=privacy_setting.allow_search_by_email,
                allow_search_by_username=privacy_setting.allow_search_by_username,
                auto_accept_from_contacts=privacy_setting.auto_accept_from_contacts,
                require_verification_message=privacy_setting.require_verification_message,
                show_online_status=privacy_setting.show_online_status,
                show_last_seen=privacy_setting.show_last_seen,
                show_profile_to_friends=privacy_setting.show_profile_to_friends,
                created_at=privacy_setting.created_at,
                updated_at=privacy_setting.updated_at
            )
            
        except Exception as e:
            logger.error(f"获取隐私设置失败: {e}")
            raise
    
    async def update_privacy_settings(self, user_id: str, settings_data: Dict[str, Any]):
        """更新隐私设置 - 占位符实现"""
        # TODO: 实现完整的隐私设置更新逻辑
        pass
    
    async def get_contact_analytics(self, user_id: str, period: str):
        """获取联系人统计 - 占位符实现"""
        # TODO: 实现完整的统计分析逻辑
        return ContactAnalyticsResponse(
            total_friends=0,
            active_friends=0,
            total_tags=0,
            total_groups=0,
            interactions_this_week=0,
            top_tags=[],
            recent_activities=[]
        )



