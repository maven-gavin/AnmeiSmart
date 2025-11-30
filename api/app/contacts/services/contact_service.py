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
        """获取好友列表（支持筛选、排序、物理分页）"""
        # 构建基础查询
        query = self.db.query(Friendship).filter(
            Friendship.user_id == user_id
        )
        
        # 应用基础筛选
        if status:
            query = query.filter(Friendship.status == status)
        elif view == "starred":
            query = query.filter(Friendship.is_starred == True)
        elif view == "blocked":
            query = query.filter(Friendship.is_blocked == True)
        elif view == "pending":
            query = query.filter(Friendship.status == "pending")
        elif view == "recent":
            # 最近联系：有 last_interaction_at 且不为空
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
        
        # 应用搜索（数据库层面）
        if search:
            need_user_join = True
            search_pattern = f"%{search}%"
            query = query.join(User, Friendship.friend_id == User.id).filter(
                or_(
                    User.username.ilike(search_pattern),
                    Friendship.nickname.ilike(search_pattern),
                    Friendship.remark.ilike(search_pattern)
                )
            )
        
        # 处理需要去重的情况（使用子查询避免 DISTINCT + ORDER BY 冲突）
        needs_distinct = tags or groups or search or (sort_by == "name")
        
        if needs_distinct:
            # 使用子查询：先选择去重后的 Friendship.id
            distinct_ids_query = query.with_entities(Friendship.id).distinct()
            # 统计总数
            total = distinct_ids_query.count()
            # 将子查询转换为子查询对象，用于后续 JOIN
            distinct_ids_subq = distinct_ids_query.subquery()
            distinct_ids_alias = aliased(distinct_ids_subq)
            # 重新构建查询：从 Friendship 表 JOIN 子查询，保留 user_id 筛选
            query = self.db.query(Friendship).filter(
                Friendship.user_id == user_id
            ).join(
                distinct_ids_alias, Friendship.id == distinct_ids_alias.c.id
            )
        else:
            # 不需要去重，直接统计
            total = query.count()
        
        # 应用排序（数据库层面）
        # 注意：如果使用了子查询，需要重新 JOIN User 表（如果需要）
        if sort_by == "name":
            # 需要 JOIN User 表来排序用户名
            if not need_user_join:
                query = query.join(User, Friendship.friend_id == User.id)
            order_expr = func.coalesce(Friendship.nickname, User.username)
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
        friendships = query.options(
            joinedload(Friendship.friend),
            joinedload(Friendship.tags).joinedload(FriendshipTag.tag),
            joinedload(Friendship.group_memberships).joinedload(ContactGroupMember.group)
        ).offset(offset).limit(size).all()
        
        # 转换为响应模型
        friendship_responses = [FriendshipResponse.from_model(f) for f in friendships]
        
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
    
    def accept_friend_request(self, friendship_id: str) -> FriendshipResponse:
        """接受好友请求"""
        friendship = self.db.query(Friendship).filter(
            Friendship.id == friendship_id
        ).first()
        
        if not friendship:
            raise BusinessException("好友关系不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
        
        if friendship.status != "pending":
            raise BusinessException("好友请求状态不正确", code=ErrorCode.INVALID_OPERATION)
        
        friendship.status = "accepted"
        friendship.accepted_at = datetime.now()
        
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
        nickname: Optional[str] = None,
        remark: Optional[str] = None,
        is_starred: Optional[bool] = None,
        is_muted: Optional[bool] = None,
        is_pinned: Optional[bool] = None
    ) -> FriendshipResponse:
        """更新好友关系"""
        friendship = self.db.query(Friendship).filter(
            Friendship.id == friendship_id
        ).first()
        
        if not friendship:
            raise BusinessException("好友关系不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
        
        # 更新字段
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
        """删除好友关系"""
        friendship = self.db.query(Friendship).filter(
            and_(
                Friendship.id == friendship_id,
                Friendship.user_id == user_id
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
    
    def get_contact_analytics_use_case(
        self,
        user_id: str,
        period: str = "month"
    ) -> Dict[str, Any]:
        """获取联系人使用统计用例"""
        # 暂时返回简单统计，后续可以扩展
        friendships = self.db.query(Friendship).filter(
            Friendship.user_id == user_id
        ).all()
        
        tags = self.db.query(ContactTag).filter(
            ContactTag.user_id == user_id
        ).count()
        
        groups = self.db.query(ContactGroup).filter(
            ContactGroup.user_id == user_id
        ).count()
        
        return {
            "total_friends": len([f for f in friendships if f.status == "accepted"]),
            "pending_requests": len([f for f in friendships if f.status == "pending"]),
            "total_tags": tags,
            "total_groups": groups,
            "period": period
        }

