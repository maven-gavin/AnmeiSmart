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
    
    async def get_friend_requests(self, user_id: str, request_type: str, status: Optional[str], page: int, size: int):
        """获取好友请求 - 占位符实现"""
        # TODO: 实现完整的好友请求获取逻辑
        return PaginatedFriendRequestsResponse(
            items=[],
            total=0,
            page=page,
            size=size,
            pages=0,
            has_next=False,
            has_prev=False
        )
    
    async def handle_friend_request(self, user_id: str, request_id: str, action: str, message: Optional[str]):
        """处理好友请求 - 占位符实现"""
        # TODO: 实现完整的好友请求处理逻辑
        pass
    
    async def update_friendship(self, user_id: str, friendship_id: str, update_data: Dict[str, Any]):
        """更新好友关系 - 占位符实现"""
        # TODO: 实现完整的好友关系更新逻辑
        pass
    
    async def delete_friendship(self, user_id: str, friendship_id: str):
        """删除好友关系 - 占位符实现"""
        # TODO: 实现完整的好友关系删除逻辑
        pass
    
    async def batch_friend_operations(self, user_id: str, friendship_ids: List[str], operation: str, operation_data: Optional[Dict[str, Any]]):
        """批量好友操作 - 占位符实现"""
        # TODO: 实现完整的批量操作逻辑
        pass
    
    async def update_contact_tag(self, user_id: str, tag_id: str, update_data: Dict[str, Any]):
        """更新联系人标签 - 占位符实现"""
        # TODO: 实现完整的标签更新逻辑
        pass
    
    async def delete_contact_tag(self, user_id: str, tag_id: str):
        """删除联系人标签 - 占位符实现"""
        # TODO: 实现完整的标签删除逻辑
        pass
    
    async def update_friend_tags(self, user_id: str, friendship_id: str, tag_ids: List[str]):
        """更新好友标签 - 占位符实现"""
        # TODO: 实现完整的好友标签更新逻辑
        pass
    
    async def get_friends_by_tag(self, user_id: str, tag_id: str, page: int, size: int):
        """获取指定标签的好友 - 占位符实现"""
        # TODO: 实现完整的标签好友获取逻辑
        pass
    
    async def get_tag_suggestions(self, user_id: str, friendship_id: Optional[str]):
        """获取标签推荐 - 占位符实现"""
        # TODO: 实现完整的标签推荐逻辑
        return []
    
    async def get_contact_groups(self, user_id: str, include_members: bool):
        """获取联系人分组 - 占位符实现"""
        # TODO: 实现完整的分组获取逻辑
        return []
    
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
    
    async def get_privacy_settings(self, user_id: str):
        """获取隐私设置 - 占位符实现"""
        # TODO: 实现完整的隐私设置获取逻辑
        pass
    
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



