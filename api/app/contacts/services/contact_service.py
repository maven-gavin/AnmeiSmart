"""
联系人服务 - 核心业务逻辑
处理好友关系、标签、分组管理等功能
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload, aliased
from sqlalchemy import and_, or_, func, desc, asc

from app.contacts.models.contacts import (
    Friendship, ContactTag, ContactGroup, ContactGroupMember, 
    FriendshipTag, ContactPrivacySetting
)
from app.contacts.schemas.contacts import (
    FriendshipResponse, ContactTagResponse, ContactGroupResponse,
    ContactTagCreate, ContactTagUpdate, UpdateFriendTagsRequest,
    CreateContactGroupRequest, UpdateContactGroupRequest,
    FriendRequestCreate, FriendRequestAction, UserSearchResult
)
# 移除 converter 导入，改用 schemas 的 from_model 方法
from app.identity_access.models.user import User
from app.common.deps.uuid_utils import friendship_id, tag_id, group_id, relation_id
from app.core.api import BusinessException, ErrorCode
from datetime import datetime

logger = logging.getLogger(__name__)


class ContactService:
    """联系人服务 - 直接操作数据库模型"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============ 好友关系管理 ============
    
    def get_friendships(
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
    ) -> Dict[str, Any]:
        """获取好友列表（支持筛选、排序、物理分页）
        
        注意：好友关系是双向的，需要查询：
        - user_id == current_user.id AND status == 'accepted' (我邀请的，已接受)
        - friend_id == current_user.id AND status == 'accepted' (我被邀请的，已接受)
        """
        # 构建基础查询：查询双向的好友关系，只查询已接受的
        base_filter = or_(
            and_(Friendship.user_id == user_id, Friendship.status == "accepted"),
            and_(Friendship.friend_id == user_id, Friendship.status == "accepted")
        )
        query = self.db.query(Friendship).filter(base_filter)
        
        # 应用基础筛选
        if status:
            # 如果指定了 status，需要重新构建查询
            if status == "accepted":
                # 已接受的好友，使用上面的 base_filter
                pass
            else:
                # 其他状态，需要重新构建
                query = self.db.query(Friendship).filter(
                    or_(
                        and_(Friendship.user_id == user_id, Friendship.status == status),
                        and_(Friendship.friend_id == user_id, Friendship.status == status)
                    )
                )
        elif view == "starred":
            # 星标好友：必须是已接受的好友且被星标
            query = query.filter(Friendship.is_starred == True)
        elif view == "blocked":
            # 屏蔽的好友
            query = query.filter(Friendship.is_blocked == True)
        elif view == "pending":
            # pending 视图应该显示已接受的好友（用于待处理请求页面，但实际应该用专门的API）
            # 这里保持原逻辑，但实际待处理请求应该通过 get_friend_requests API
            query = self.db.query(Friendship).filter(
                or_(
                    and_(Friendship.user_id == user_id, Friendship.status == "pending"),
                    and_(Friendship.friend_id == user_id, Friendship.status == "pending")
                )
            )
        elif view == "recent":
            # 最近联系：必须是已接受的好友且有 last_interaction_at
            query = query.filter(Friendship.last_interaction_at.isnot(None))
        
        # 应用标签筛选（数据库层面）
        if tags:
            query = query.join(FriendshipTag).filter(
                FriendshipTag.tag_id.in_(tags)
            )
        
        # 应用分组筛选（数据库层面）
        if groups:
            query = query.join(ContactGroupMember).filter(
                ContactGroupMember.group_id.in_(groups)
            )
        
        # 标记是否需要 JOIN User 表（用于搜索或排序）
        need_user_join = False
        friend_user_alias = None
        user_user_alias = None
        
        # 应用搜索（数据库层面）
        # 需要支持双向搜索：当 user_id == current_user 时搜索 friend，当 friend_id == current_user 时搜索 user
        if search:
            need_user_join = True
            search_pattern = f"%{search}%"
            # 创建两个别名用于 JOIN：一个用于 friend（当 user_id == current_user），一个用于 user（当 friend_id == current_user）
            friend_user_alias = aliased(User, name="friend_user")
            user_user_alias = aliased(User, name="user_user")
            # 使用 CASE 表达式确保每个 Friendship 只 JOIN 一个 User
            # 当 user_id == user_id 时，JOIN friend_user；当 friend_id == user_id 时，JOIN user_user
            query = query.outerjoin(
                friend_user_alias, and_(
                    Friendship.friend_id == friend_user_alias.id,
                    Friendship.user_id == user_id
                )
            ).outerjoin(
                user_user_alias, and_(
                    Friendship.user_id == user_user_alias.id,
                    Friendship.friend_id == user_id
                )
            ).filter(
                or_(
                    friend_user_alias.username.ilike(search_pattern),
                    user_user_alias.username.ilike(search_pattern),
                    Friendship.nickname.ilike(search_pattern),
                    Friendship.remark.ilike(search_pattern)
                )
            )
        
        # 处理需要去重的情况（使用子查询避免 DISTINCT + ORDER BY 冲突）
        # 当有标签、分组、搜索或按名称排序时，JOIN 操作可能导致重复，需要去重
        needs_distinct = tags or groups or search or (sort_by == "name")
        
        if needs_distinct:
            # 使用子查询：先选择去重后的 Friendship.id
            distinct_ids_query = query.with_entities(Friendship.id).distinct()
            # 统计总数
            total = distinct_ids_query.count()
            # 将子查询转换为子查询对象，用于后续 JOIN
            distinct_ids_subq = distinct_ids_query.subquery()
            distinct_ids_alias = aliased(distinct_ids_subq)
            # 重新构建查询：从 Friendship 表 JOIN 子查询，保留双向筛选
            # 使用 INNER JOIN 确保只返回去重后的记录
            query = self.db.query(Friendship).filter(
                or_(
                    and_(Friendship.user_id == user_id, Friendship.status == "accepted"),
                    and_(Friendship.friend_id == user_id, Friendship.status == "accepted")
                )
            ).join(
                distinct_ids_alias, Friendship.id == distinct_ids_alias.c.id
            )
            # 如果使用了子查询，需要重新 JOIN User 表（如果之前 JOIN 过或需要排序）
            if need_user_join or sort_by == "name":
                friend_user_alias = aliased(User, name="friend_user")
                user_user_alias = aliased(User, name="user_user")
                query = query.outerjoin(
                    friend_user_alias, and_(
                        Friendship.friend_id == friend_user_alias.id,
                        Friendship.user_id == user_id
                    )
                ).outerjoin(
                    user_user_alias, and_(
                        Friendship.user_id == user_user_alias.id,
                        Friendship.friend_id == user_id
                    )
                )
        else:
            # 不需要去重，直接统计
            # 但为了安全起见，仍然使用 distinct() 确保没有重复
            total = query.distinct().count()
            query = query.distinct()
        
        # 应用排序（数据库层面）
        # 注意：如果使用了子查询，需要重新 JOIN User 表（如果需要）
        if sort_by == "name":
            # 需要 JOIN User 表来排序用户名，支持双向查询
            if not need_user_join and friend_user_alias is None:
                # 创建两个别名用于 JOIN
                friend_user_alias = aliased(User, name="friend_user")
                user_user_alias = aliased(User, name="user_user")
                query = query.outerjoin(
                    friend_user_alias, and_(
                        Friendship.friend_id == friend_user_alias.id,
                        Friendship.user_id == user_id
                    )
                ).outerjoin(
                    user_user_alias, and_(
                        Friendship.user_id == user_user_alias.id,
                        Friendship.friend_id == user_id
                    )
                )
            # 使用 COALESCE 处理双向情况：优先使用 friend_user，如果没有则使用 user_user
            order_expr = func.coalesce(
                Friendship.nickname,
                func.coalesce(friend_user_alias.username, user_user_alias.username)
            )
            if sort_order == "desc":
                query = query.order_by(desc(order_expr))
            else:
                query = query.order_by(asc(order_expr))
        elif sort_by == "recent":
            if sort_order == "desc":
                query = query.order_by(desc(func.coalesce(Friendship.last_interaction_at, Friendship.created_at)))
            else:
                query = query.order_by(asc(func.coalesce(Friendship.last_interaction_at, Friendship.created_at)))
        elif sort_by == "added":
            if sort_order == "desc":
                query = query.order_by(desc(Friendship.created_at))
            else:
                query = query.order_by(asc(Friendship.created_at))
        elif sort_by == "interaction":
            if sort_order == "desc":
                query = query.order_by(desc(Friendship.interaction_count))
            else:
                query = query.order_by(asc(Friendship.interaction_count))
        else:
            # 默认按创建时间倒序
            query = query.order_by(desc(Friendship.created_at))
        
        # 应用物理分页
        offset = (page - 1) * size
        # 确保在加载关联数据前已经去重
        # 使用 distinct() 确保没有重复的 Friendship 记录
        friendships = query.distinct().options(
            joinedload(Friendship.friend),
            joinedload(Friendship.user),
            joinedload(Friendship.tags).joinedload(FriendshipTag.tag),
            joinedload(Friendship.group_memberships).joinedload(ContactGroupMember.group)
        ).offset(offset).limit(size).all()
        
        # 转换为响应模型
        # 需要处理双向关系：确保 friend 字段始终表示当前用户的好友
        # 使用字典去重，基于 Friendship.id，确保每个好友只出现一次
        seen_friendship_ids = set()
        friendship_responses = []
        for f in friendships:
            # 如果已经处理过这个 Friendship，跳过
            if f.id in seen_friendship_ids:
                continue
            seen_friendship_ids.add(f.id)
            # 如果 friend_id == user_id，说明当前用户是被邀请者，那么 user 才是好友
            if f.friend_id == user_id:
                # 当前用户是被邀请者，需要交换 user 和 friend
                # 注意：数据库中只有一条记录，nickname 和 remark 是邀请者（f.user_id）设置的
                # 对于被邀请者（current_user），这些字段应该为空，因为被邀请者还没有设置
                # 创建一个规范化后的 friendship 对象用于转换
                normalized_friendship = type('NormalizedFriendship', (), {
                    'id': f.id,
                    'user_id': user_id,  # 当前用户始终是 user_id
                    'friend_id': f.user_id,  # 原来的 user_id 变成 friend_id
                    'status': f.status,
                    'source': f.source,
                    # 被邀请者视角：nickname 和 remark 应该为空（因为这些是邀请者设置的）
                    'nickname': None,  # 被邀请者还没有设置昵称
                    'remark': None,  # 被邀请者还没有设置备注
                    # 使用当前记录的设置（这些是相对于 user_id 的，但我们需要从被邀请者视角）
                    # 注意：is_starred、is_muted 等是相对于 user_id 的，所以对于被邀请者应该使用默认值
                    'is_starred': False,  # 被邀请者还没有设置星标
                    'is_muted': False,  # 被邀请者还没有设置免打扰
                    'is_pinned': False,  # 被邀请者还没有设置置顶
                    'is_blocked': f.is_blocked,  # 屏蔽状态可以共享
                    'requested_at': f.requested_at,
                    'accepted_at': f.accepted_at,
                    'last_interaction_at': f.last_interaction_at,
                    'interaction_count': f.interaction_count or 0,
                    'created_at': f.created_at,
                    'updated_at': f.updated_at,
                    'friend': f.user,  # 原来的 user 变成 friend
                    'tags': f.tags or [],  # 标签是相对于 friendship 的，可以共享
                    'group_memberships': f.group_memberships
                })()
            else:
                # 当前用户是邀请者，friend 就是好友，直接使用原对象
                normalized_friendship = f
            
            friendship_responses.append(FriendshipResponse.from_model(normalized_friendship))
        
        total_pages = (total + size - 1) // size if total > 0 else 0
        
        return {
            "items": friendship_responses,
            "total": total,
            "page": page,
            "size": size,
            "pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    
    def send_friend_request(
        self,
        user_id: str,
        friend_id: str,
        verification_message: Optional[str] = None,
        source: str = "manual"
    ) -> FriendshipResponse:
        """发送好友请求"""
        # 检查好友关系是否已存在
        existing = self.db.query(Friendship).filter(
            and_(
                Friendship.user_id == user_id,
                Friendship.friend_id == friend_id
            )
        ).first()
        
        if existing:
            raise BusinessException("好友关系已存在", code=ErrorCode.BUSINESS_ERROR)
        
        # 创建好友关系（状态为pending）
        friendship = Friendship(
            id=friendship_id(),
            user_id=user_id,
            friend_id=friend_id,
            status="pending",
            remark=verification_message,
            source=source
        )
        
        self.db.add(friendship)
        self.db.commit()
        self.db.refresh(friendship)
        
        # 加载关联数据
        friendship = self.db.query(Friendship).filter(
            Friendship.id == friendship.id
        ).options(
            joinedload(Friendship.friend),
            joinedload(Friendship.tags).joinedload(FriendshipTag.tag)
        ).first()
        
        return FriendshipResponse.from_model(friendship)
    
    def update_friendship(
        self,
        friendship_id: str,
        user_id: str,
        nickname: Optional[str] = None,
        remark: Optional[str] = None,
        is_starred: Optional[bool] = None,
        is_muted: Optional[bool] = None,
        is_pinned: Optional[bool] = None
    ) -> FriendshipResponse:
        """更新好友关系（支持双向更新）"""
        # 查询好友关系，支持双向：user_id 或 friend_id 是当前用户
        friendship = self.db.query(Friendship).filter(
            and_(
                Friendship.id == friendship_id,
                or_(
                    Friendship.user_id == user_id,
                    Friendship.friend_id == user_id
                )
            )
        ).first()
        
        if not friendship:
            raise BusinessException("好友关系不存在或无权限", code=ErrorCode.RESOURCE_NOT_FOUND)
        
        # 确定当前用户是邀请者还是被邀请者
        is_inviter = friendship.user_id == user_id
        
        # 更新字段
        # 注意：nickname 和 remark 是相对于 user_id 的，只有邀请者可以设置
        # 如果当前用户是被邀请者，这些字段不应该更新
        if is_inviter:
            # 当前用户是邀请者，可以更新所有字段
            if nickname is not None:
                friendship.nickname = nickname
            if remark is not None:
                friendship.remark = remark
            if is_starred is not None:
                friendship.is_starred = is_starred
            if is_muted is not None:
                friendship.is_muted = is_muted
            if is_pinned is not None:
                friendship.is_pinned = is_pinned
        else:
            # 当前用户是被邀请者，只能更新自己的设置
            # 注意：被邀请者无法设置 nickname 和 remark（这些是邀请者设置的）
            if nickname is not None or remark is not None:
                logger.warning(f"被邀请者尝试更新 nickname 或 remark，已忽略: friendship_id={friendship_id}, user_id={user_id}")
            if is_starred is not None:
                # 被邀请者无法设置星标（因为这是相对于 user_id 的）
                logger.warning(f"被邀请者尝试更新 is_starred，已忽略: friendship_id={friendship_id}, user_id={user_id}")
            if is_muted is not None:
                friendship.is_muted = is_muted
            if is_pinned is not None:
                friendship.is_pinned = is_pinned
        
        self.db.commit()
        self.db.refresh(friendship)
        
        # 加载关联数据
        friendship = self.db.query(Friendship).filter(
            Friendship.id == friendship.id
        ).options(
            joinedload(Friendship.friend),
            joinedload(Friendship.user),
            joinedload(Friendship.tags).joinedload(FriendshipTag.tag)
        ).first()
        
        return FriendshipResponse.from_model(friendship)
    
    # ============ 标签管理 ============
    
    def get_contact_tags(self, user_id: str) -> List[ContactTagResponse]:
        """获取用户的联系人标签"""
        tags = self.db.query(ContactTag).filter(
            ContactTag.user_id == user_id
        ).order_by(ContactTag.display_order.asc(), ContactTag.name.asc()).all()
        
        return [ContactTagResponse.from_model(tag) for tag in tags]
    
    def create_contact_tag(self, user_id: str, tag_data: ContactTagCreate) -> ContactTagResponse:
        """创建联系人标签"""
        # 检查标签名称是否重复
        existing = self.db.query(ContactTag).filter(
            and_(
                ContactTag.user_id == user_id,
                ContactTag.name == tag_data.name
            )
        ).first()
        
        if existing:
            raise BusinessException("标签名称已存在", code=ErrorCode.BUSINESS_ERROR)
        
        # 创建标签
        tag = ContactTag(
            id=tag_id(),
            user_id=user_id,
            name=tag_data.name,
            color=tag_data.color,
            icon=tag_data.icon,
            description=tag_data.description,
            category=tag_data.category.value if hasattr(tag_data.category, 'value') else tag_data.category,
            display_order=tag_data.display_order,
            is_visible=tag_data.is_visible
        )
        
        self.db.add(tag)
        self.db.commit()
        self.db.refresh(tag)
        
        return ContactTagResponse.from_model(tag)
    
    def update_contact_tag(self, tag_id: str, tag_data: ContactTagUpdate) -> ContactTagResponse:
        """更新联系人标签"""
        tag = self.db.query(ContactTag).filter(
            ContactTag.id == tag_id
        ).first()
        
        if not tag:
            raise BusinessException("标签不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
        
        # 更新字段
        update_dict = tag_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if key == "category" and hasattr(value, 'value'):
                setattr(tag, key, value.value)
            else:
                setattr(tag, key, value)
        
        self.db.commit()
        self.db.refresh(tag)
        
        return ContactTagResponse.from_model(tag)
    
    def update_friend_tags(self, friendship_id: str, tag_ids: List[str]) -> FriendshipResponse:
        """更新好友标签"""
        friendship = self.db.query(Friendship).filter(
            Friendship.id == friendship_id
        ).options(
            joinedload(Friendship.tags)
        ).first()
        
        if not friendship:
            raise BusinessException("好友关系不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
        
        # 删除现有标签
        self.db.query(FriendshipTag).filter(
            FriendshipTag.friendship_id == friendship_id
        ).delete()
        
        # 添加新标签
        for tag_id_str in tag_ids:
            tag = self.db.query(ContactTag).filter(ContactTag.id == tag_id_str).first()
            if tag:
                friendship_tag = FriendshipTag(
                    id=relation_id(),
                    friendship_id=friendship_id,
                    tag_id=tag_id_str
                )
                self.db.add(friendship_tag)
                
                # 更新标签使用次数
                tag.usage_count = (tag.usage_count or 0) + 1
        
        self.db.commit()
        
        # 重新加载关联数据
        friendship = self.db.query(Friendship).filter(
            Friendship.id == friendship_id
        ).options(
            joinedload(Friendship.friend),
            joinedload(Friendship.tags).joinedload(FriendshipTag.tag)
        ).first()
        
        return FriendshipResponse.from_model(friendship)
    
    # ============ 分组管理 ============
    
    def get_contact_groups(self, user_id: str) -> List[ContactGroupResponse]:
        """获取用户的联系人分组"""
        groups = self.db.query(ContactGroup).filter(
            ContactGroup.user_id == user_id
        ).options(
            joinedload(ContactGroup.members).joinedload(ContactGroupMember.friendship)
        ).order_by(ContactGroup.display_order.asc(), ContactGroup.name.asc()).all()
        
        return [ContactGroupResponse.from_model(g, include_members=True) for g in groups]
    
    def create_contact_group(self, user_id: str, group_data: CreateContactGroupRequest) -> ContactGroupResponse:
        """创建联系人分组"""
        # 检查分组名称是否重复
        existing = self.db.query(ContactGroup).filter(
            and_(
                ContactGroup.user_id == user_id,
                ContactGroup.name == group_data.name
            )
        ).first()
        
        if existing:
            raise BusinessException("分组名称已存在", code=ErrorCode.BUSINESS_ERROR)
        
        # 创建分组
        group = ContactGroup(
            id=group_id(),
            user_id=user_id,
            name=group_data.name,
            description=group_data.description,
            avatar=getattr(group_data, 'avatar', None),
            group_type=getattr(group_data, 'group_type', 'personal'),
            color_theme=getattr(group_data, 'color_theme', '#3B82F6'),
            display_order=getattr(group_data, 'display_order', 0),
            is_collapsed=getattr(group_data, 'is_collapsed', False),
            max_members=getattr(group_data, 'max_members', None),
            is_private=getattr(group_data, 'is_private', False)
        )
        
        self.db.add(group)
        self.db.commit()
        self.db.refresh(group)
        
        return ContactGroupResponse.from_model(group)
    
    def update_contact_group(self, group_id: str, group_data: UpdateContactGroupRequest) -> ContactGroupResponse:
        """更新联系人分组"""
        group = self.db.query(ContactGroup).filter(
            ContactGroup.id == group_id
        ).first()
        
        if not group:
            raise BusinessException("分组不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
        
        # 更新字段
        update_dict = group_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(group, key, value)
        
        self.db.commit()
        self.db.refresh(group)
        
        return ContactGroupResponse.from_model(group)
    
    def delete_contact_group(self, group_id: str, user_id: str) -> bool:
        """删除联系人分组"""
        group = self.db.query(ContactGroup).filter(
            and_(
                ContactGroup.id == group_id,
                ContactGroup.user_id == user_id
            )
        ).first()
        
        if not group:
            raise BusinessException("分组不存在或无权限", code=ErrorCode.RESOURCE_NOT_FOUND)
        
        # 删除关联的成员
        self.db.query(ContactGroupMember).filter(
            ContactGroupMember.group_id == group_id
        ).delete()
        
        self.db.delete(group)
        self.db.commit()
        return True
    
    def delete_contact_tag(self, tag_id: str, user_id: str) -> bool:
        """删除联系人标签"""
        tag = self.db.query(ContactTag).filter(
            and_(
                ContactTag.id == tag_id,
                ContactTag.user_id == user_id
            )
        ).first()
        
        if not tag:
            raise BusinessException("标签不存在或无权限", code=ErrorCode.RESOURCE_NOT_FOUND)
        
        # 删除关联的好友标签
        self.db.query(FriendshipTag).filter(
            FriendshipTag.tag_id == tag_id
        ).delete()
        
        self.db.delete(tag)
        self.db.commit()
        return True
    
    def delete_friendship(self, friendship_id: str, user_id: str) -> bool:
        """删除好友关系（支持双向删除）"""
        # 查询好友关系，支持双向：user_id 或 friend_id 是当前用户
        friendship = self.db.query(Friendship).filter(
            and_(
                Friendship.id == friendship_id,
                or_(
                    Friendship.user_id == user_id,
                    Friendship.friend_id == user_id
                )
            )
        ).first()
        
        if not friendship:
            raise BusinessException("好友关系不存在或无权限", code=ErrorCode.RESOURCE_NOT_FOUND)
        
        # 删除关联的标签和分组成员
        self.db.query(FriendshipTag).filter(
            FriendshipTag.friendship_id == friendship_id
        ).delete()
        
        self.db.query(ContactGroupMember).filter(
            ContactGroupMember.friendship_id == friendship_id
        ).delete()
        
        self.db.delete(friendship)
        self.db.commit()
        return True
    
    def handle_friend_request(
        self,
        request_id: str,
        user_id: str,
        action: str,
        message: Optional[str] = None
    ) -> FriendshipResponse:
        """处理好友请求（接受/拒绝）"""
        friendship = self.db.query(Friendship).filter(
            Friendship.id == request_id
        ).first()
        
        if not friendship:
            raise BusinessException("好友请求不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
        
        # 验证权限：只有被请求的用户才能处理
        if friendship.friend_id != user_id:
            raise BusinessException("无权处理此好友请求", code=ErrorCode.PERMISSION_DENIED)
        
        if friendship.status != "pending":
            raise BusinessException("好友请求状态不正确", code=ErrorCode.INVALID_OPERATION)
        
        if action == "accept":
            friendship.status = "accepted"
            friendship.accepted_at = datetime.now()
        elif action == "reject":
            friendship.status = "rejected"
            friendship.rejected_at = datetime.now()
        else:
            raise BusinessException("无效的操作", code=ErrorCode.INVALID_OPERATION)
        
        if message:
            friendship.remark = message
        
        self.db.commit()
        self.db.refresh(friendship)
        
        # 加载关联数据
        friendship = self.db.query(Friendship).filter(
            Friendship.id == friendship.id
        ).options(
            joinedload(Friendship.friend),
            joinedload(Friendship.tags).joinedload(FriendshipTag.tag)
        ).first()
        
        return FriendshipResponse.from_model(friendship)
    
    def search_users(
        self,
        current_user_id: str,
        query: str,
        search_type: str = "all",
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """搜索用户（用于添加好友）"""
        from app.identity_access.models.user import User
        
        # 搜索用户（暂时简化实现，后续可以优化）
        search_term = f"%{query}%"
        users = self.db.query(User).filter(
            and_(
                User.id != current_user_id,  # 排除自己
                or_(
                    User.username.ilike(search_term),
                    User.email.ilike(search_term),
                    User.phone.ilike(search_term) if User.phone else False
                )
            )
        ).limit(limit).all()
        
        # 转换为响应格式
        result = []
        for user in users:
            result.append({
                "id": user.id,
                "name": user.username,  # UserSearchResult 期望 name 字段
                "email": user.email,
                "avatar": user.avatar,
                "phone": user.phone
            })
        return result
    
    # ============ 用例方法（适配旧接口） ============
    
    def search_users_use_case(
        self,
        current_user_id: str,
        query: str,
        search_type: str = "all",
        limit: int = 20
    ) -> List[UserSearchResult]:
        """搜索用户用例"""
        return self.search_users(
            current_user_id=current_user_id,
            query=query,
            search_type=search_type,
            limit=limit
        )
    
    def send_friend_request_use_case(
        self,
        user_id: str,
        friend_id: str,
        verification_message: Optional[str] = None,
        source: str = "manual"
    ) -> Dict[str, Any]:
        """发送好友请求用例"""
        friendship_response = self.send_friend_request(
            user_id=user_id,
            friend_id=friend_id,
            verification_message=verification_message,
            source=source
        )
        
        return {
            "id": friendship_response.id,
            "user_id": friendship_response.user_id,
            "friend_id": friendship_response.friend_id,
            "status": friendship_response.status,
            "verification_message": getattr(friendship_response, 'remark', verification_message),
            "source": getattr(friendship_response, 'source', source),
            "created_at": friendship_response.created_at,
            "requested_at": friendship_response.requested_at or friendship_response.created_at  # 添加 requested_at
        }
    
    def handle_friend_request_use_case(
        self,
        user_id: str,
        request_id: str,
        action: str,
        message: Optional[str] = None
    ) -> None:
        """处理好友请求用例"""
        self.handle_friend_request(
            request_id=request_id,
            user_id=user_id,
            action=action,
            message=message
        )
    
    def update_friendship_use_case(
        self,
        user_id: str,
        friendship_id: str,
        update_data: Dict[str, Any]
    ) -> FriendshipResponse:
        """更新好友关系用例"""
        return self.update_friendship(
            friendship_id=friendship_id,
            user_id=user_id,
            nickname=update_data.get("nickname"),
            remark=update_data.get("remark"),
            is_starred=update_data.get("is_starred"),
            is_muted=update_data.get("is_muted"),
            is_pinned=update_data.get("is_pinned")
        )
    
    def delete_friendship_use_case(
        self,
        user_id: str,
        friendship_id: str
    ) -> None:
        """删除好友关系用例"""
        self.delete_friendship(friendship_id=friendship_id, user_id=user_id)
    
    def get_contact_tags_use_case(
        self,
        user_id: str,
        category: Optional[str] = None,
        include_system: bool = True
    ) -> List[ContactTagResponse]:
        """获取联系人标签用例"""
        tags = self.get_contact_tags(user_id=user_id)
        
        # 应用分类筛选
        if category:
            tags = [t for t in tags if getattr(t, 'category', None) == category]
        
        return tags
    
    def create_contact_tag_use_case(
        self,
        user_id: str,
        tag_data: ContactTagCreate
    ) -> ContactTagResponse:
        """创建联系人标签用例"""
        return self.create_contact_tag(user_id=user_id, tag_data=tag_data)
    
    def update_contact_tag_use_case(
        self,
        user_id: str,
        tag_id: str,
        update_data: Dict[str, Any]
    ) -> ContactTagResponse:
        """更新联系人标签用例"""
        from app.contacts.schemas.contacts import ContactTagUpdate
        tag_update = ContactTagUpdate(**update_data)
        return self.update_contact_tag(tag_id=tag_id, tag_data=tag_update)
    
    def delete_contact_tag_use_case(
        self,
        user_id: str,
        tag_id: str
    ) -> None:
        """删除联系人标签用例"""
        self.delete_contact_tag(tag_id=tag_id, user_id=user_id)
    
    def get_contact_groups_use_case(
        self,
        user_id: str,
        include_members: bool = False
    ) -> List[ContactGroupResponse]:
        """获取联系人分组用例"""
        return self.get_contact_groups(user_id=user_id)
    
    def create_contact_group_use_case(
        self,
        user_id: str,
        group_data: CreateContactGroupRequest
    ) -> ContactGroupResponse:
        """创建联系人分组用例"""
        return self.create_contact_group(user_id=user_id, group_data=group_data)
    
    def update_contact_group_use_case(
        self,
        user_id: str,
        group_id: str,
        update_data: Dict[str, Any]
    ) -> ContactGroupResponse:
        """更新联系人分组用例"""
        from app.contacts.schemas.contacts import UpdateContactGroupRequest
        group_update = UpdateContactGroupRequest(**update_data)
        return self.update_contact_group(group_id=group_id, group_data=group_update)
    
    def delete_contact_group_use_case(
        self,
        user_id: str,
        group_id: str
    ) -> None:
        """删除联系人分组用例"""
        self.delete_contact_group(group_id=group_id, user_id=user_id)
    
    def get_friend_requests(
        self,
        user_id: str,
        request_type: str = "received",
        status: Optional[str] = None,
        page: int = 1,
        size: int = 20
    ) -> Dict[str, Any]:
        """获取好友请求列表"""
        from app.contacts.schemas.contacts import FriendRequestResponse
        
        # 构建查询
        if request_type == "received":
            # 收到的请求：friend_id 是当前用户
            query = self.db.query(Friendship).filter(
                Friendship.friend_id == user_id
            )
        elif request_type == "sent":
            # 发送的请求：user_id 是当前用户
            query = self.db.query(Friendship).filter(
                Friendship.user_id == user_id
            )
        else:
            raise BusinessException("无效的请求类型", code=ErrorCode.INVALID_PARAMETER)
        
        # 应用状态筛选
        if status:
            query = query.filter(Friendship.status == status)
        else:
            # 默认只查询 pending 状态的请求
            query = query.filter(Friendship.status == "pending")
        
        # 统计总数
        total = query.count()
        
        # 应用分页
        offset = (page - 1) * size
        # 注意：Friendship.user 关系可能不存在，需要检查模型定义
        # 如果不存在，我们需要手动查询用户信息
        friendships = query.options(
            joinedload(Friendship.friend)
        ).order_by(desc(Friendship.created_at)).offset(offset).limit(size).all()
        
        # 转换为响应模型
        request_responses = []
        for f in friendships:
            # 构建用户信息
            user_info = None
            friend_info = None
            
            # 手动查询发送请求的用户（user_id 对应的用户）
            if f.user_id:
                user = self.db.query(User).filter(User.id == f.user_id).first()
                if user:
                    user_info = {
                        "id": user.id,
                        "username": user.username,
                        "avatar": user.avatar,
                        "email": user.email
                    }
            
            # 接收请求的用户（friend_id 对应的用户）
            if f.friend:
                friend_info = {
                    "id": f.friend.id,
                    "username": f.friend.username,
                    "avatar": f.friend.avatar,
                    "email": f.friend.email
                }
            
            request_responses.append({
                "id": f.id,
                "user_id": f.user_id,
                "friend_id": f.friend_id,
                "status": f.status,
                "verification_message": f.remark,
                "source": f.source,
                "requested_at": f.requested_at or f.created_at,
                "user": user_info,
                "friend": friend_info
            })
        
        total_pages = (total + size - 1) // size if total > 0 else 0
        
        return {
            "items": request_responses,
            "total": total,
            "page": page,
            "size": size,
            "pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    
    def get_contact_analytics_use_case(
        self,
        user_id: str,
        period: str = "month"
    ) -> Dict[str, Any]:
        """获取联系人使用统计用例（支持双向关系统计）"""
        # 查询双向的好友关系
        friendships = self.db.query(Friendship).filter(
            or_(
                and_(Friendship.user_id == user_id, Friendship.status == "accepted"),
                and_(Friendship.friend_id == user_id, Friendship.status == "accepted")
            )
        ).all()
        
        # 查询待处理请求（收到的和发送的）
        pending_received = self.db.query(Friendship).filter(
            and_(Friendship.friend_id == user_id, Friendship.status == "pending")
        ).count()
        pending_sent = self.db.query(Friendship).filter(
            and_(Friendship.user_id == user_id, Friendship.status == "pending")
        ).count()
        
        tags = self.db.query(ContactTag).filter(
            ContactTag.user_id == user_id
        ).count()
        
        groups = self.db.query(ContactGroup).filter(
            ContactGroup.user_id == user_id
        ).count()
        
        return {
            "total_friends": len(friendships),
            "pending_requests": pending_received + pending_sent,
            "total_tags": tags,
            "total_groups": groups,
            "period": period
        }

