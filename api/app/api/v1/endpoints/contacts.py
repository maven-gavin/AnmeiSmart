"""
通讯录管理API端点
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.models.user import User
from app.api.deps import get_current_user
from app.schemas.contacts import (
    # 好友管理相关
    FriendRequestCreate,
    FriendRequestAction,
    FriendRequestResponse,
    FriendshipResponse,
    UpdateFriendshipRequest,
    UserSearchRequest,
    UserSearchResult,
    PaginatedFriendsResponse,
    PaginatedFriendRequestsResponse,
    
    # 标签管理相关
    ContactTagCreate,
    ContactTagUpdate,
    ContactTagResponse,
    UpdateFriendTagsRequest,
    TagSuggestionResponse,
    
    # 分组管理相关
    CreateContactGroupRequest,
    UpdateContactGroupRequest,
    ContactGroupResponse,
    UpdateGroupMembersRequest,
    GroupMemberResponse,
    PaginatedGroupMembersResponse,
    CreateGroupChatRequest,
    
    # 隐私设置相关
    UpdatePrivacySettingsRequest,
    ContactPrivacyResponse,
    
    # 批量操作相关
    BatchFriendOperations,
    BatchOperationResponse,
    
    # 统计分析相关
    ContactAnalyticsResponse
)
from app.services.contacts.contact_service import ContactService
from app.services.contacts.conversation_service import ContactConversationService

router = APIRouter()


# ============================================================================
# 好友管理相关API
# ============================================================================

@router.get("/friends", response_model=PaginatedFriendsResponse)
async def get_friends(
    # 筛选参数
    view: Optional[str] = Query(None, description="视图类型：all/starred/recent/blocked/pending"),
    tags: Optional[List[str]] = Query(None, description="标签ID列表筛选"),
    groups: Optional[List[str]] = Query(None, description="分组ID列表筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[str] = Query(None, description="关系状态筛选"),
    
    # 排序参数
    sort_by: str = Query("name", description="排序字段：name/recent/added/interaction"),
    sort_order: str = Query("asc", description="排序方向：asc/desc"),
    
    # 分页参数
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    
    # 依赖注入
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取好友列表（支持多维度筛选和排序）"""
    contact_service = ContactService(db)
    
    try:
        result = await contact_service.get_friends(
            user_id=current_user.id,
            view=view,
            tags=tags,
            groups=groups,
            search=search,
            status=status,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            size=size
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取好友列表失败")


@router.post("/friends/search", response_model=List[UserSearchResult])
async def search_users(
    search_request: UserSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """搜索用户（用于添加好友）"""
    contact_service = ContactService(db)
    
    try:
        result = await contact_service.search_users(
            current_user_id=current_user.id,
            query=search_request.query,
            search_type=search_request.search_type,
            limit=search_request.limit
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="搜索用户失败")


@router.post("/friends/request", response_model=FriendRequestResponse)
async def send_friend_request(
    request: FriendRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """发送好友请求"""
    contact_service = ContactService(db)
    
    try:
        result = await contact_service.send_friend_request(
            user_id=current_user.id,
            friend_id=request.friend_id,
            verification_message=request.verification_message,
            source=request.source
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="发送好友请求失败")


@router.get("/friends/requests", response_model=PaginatedFriendRequestsResponse)
async def get_friend_requests(
    type: str = Query("received", description="请求类型：sent/received"),
    status: Optional[str] = Query(None, description="请求状态筛选"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取好友请求列表"""
    contact_service = ContactService(db)
    
    try:
        result = await contact_service.get_friend_requests(
            user_id=current_user.id,
            request_type=type,
            status=status,
            page=page,
            size=size
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取好友请求失败")


@router.put("/friends/requests/{request_id}")
async def handle_friend_request(
    request_id: str,
    action: FriendRequestAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """处理好友请求（接受/拒绝）"""
    contact_service = ContactService(db)
    
    try:
        await contact_service.handle_friend_request(
            user_id=current_user.id,
            request_id=request_id,
            action=action.action,
            message=action.message
        )
        return {"message": "好友请求处理成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="处理好友请求失败")


@router.put("/friends/{friendship_id}", response_model=FriendshipResponse)
async def update_friendship(
    friendship_id: str,
    update_data: UpdateFriendshipRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新好友关系信息"""
    contact_service = ContactService(db)
    
    try:
        result = await contact_service.update_friendship(
            user_id=current_user.id,
            friendship_id=friendship_id,
            update_data=update_data.dict(exclude_unset=True)
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="更新好友关系失败")


@router.delete("/friends/{friendship_id}")
async def delete_friendship(
    friendship_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除好友关系"""
    contact_service = ContactService(db)
    
    try:
        await contact_service.delete_friendship(
            user_id=current_user.id,
            friendship_id=friendship_id
        )
        return {"message": "好友关系删除成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="删除好友关系失败")


@router.post("/friends/batch", response_model=BatchOperationResponse)
async def batch_friend_operations(
    operations: BatchFriendOperations,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量好友操作（添加标签、移动分组等）"""
    contact_service = ContactService(db)
    
    try:
        result = await contact_service.batch_friend_operations(
            user_id=current_user.id,
            friendship_ids=operations.friendship_ids,
            operation=operations.operation,
            operation_data=operations.operation_data
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="批量操作失败")


# ============================================================================
# 标签管理相关API
# ============================================================================

@router.get("/tags", response_model=List[ContactTagResponse])
async def get_contact_tags(
    category: Optional[str] = Query(None, description="标签分类筛选"),
    include_system: bool = Query(True, description="是否包含系统标签"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的联系人标签"""
    contact_service = ContactService(db)
    
    try:
        result = await contact_service.get_contact_tags(
            user_id=current_user.id,
            category=category,
            include_system=include_system
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取标签列表失败")


@router.post("/tags", response_model=ContactTagResponse)
async def create_contact_tag(
    tag_data: ContactTagCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建联系人标签"""
    contact_service = ContactService(db)
    
    try:
        result = await contact_service.create_contact_tag(
            user_id=current_user.id,
            tag_data=tag_data
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="创建标签失败")


@router.put("/tags/{tag_id}", response_model=ContactTagResponse)
async def update_contact_tag(
    tag_id: str,
    update_data: ContactTagUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新联系人标签"""
    contact_service = ContactService(db)
    
    try:
        result = await contact_service.update_contact_tag(
            user_id=current_user.id,
            tag_id=tag_id,
            update_data=update_data.dict(exclude_unset=True)
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="更新标签失败")


@router.delete("/tags/{tag_id}")
async def delete_contact_tag(
    tag_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除联系人标签"""
    contact_service = ContactService(db)
    
    try:
        await contact_service.delete_contact_tag(
            user_id=current_user.id,
            tag_id=tag_id
        )
        return {"message": "标签删除成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="删除标签失败")


@router.put("/friends/{friendship_id}/tags")
async def update_friend_tags(
    friendship_id: str,
    tag_update: UpdateFriendTagsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新好友标签"""
    contact_service = ContactService(db)
    
    try:
        await contact_service.update_friend_tags(
            user_id=current_user.id,
            friendship_id=friendship_id,
            tag_ids=tag_update.tag_ids
        )
        return {"message": "好友标签更新成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="更新好友标签失败")


@router.get("/tags/{tag_id}/friends", response_model=PaginatedFriendsResponse)
async def get_friends_by_tag(
    tag_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定标签的好友列表"""
    contact_service = ContactService(db)
    
    try:
        result = await contact_service.get_friends_by_tag(
            user_id=current_user.id,
            tag_id=tag_id,
            page=page,
            size=size
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取标签好友失败")


@router.get("/tags/suggestions", response_model=List[TagSuggestionResponse])
async def get_tag_suggestions(
    friendship_id: Optional[str] = Query(None, description="为特定好友推荐标签"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取智能标签推荐"""
    contact_service = ContactService(db)
    
    try:
        result = await contact_service.get_tag_suggestions(
            user_id=current_user.id,
            friendship_id=friendship_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取标签推荐失败")


# ============================================================================
# 分组管理相关API
# ============================================================================

@router.get("/groups", response_model=List[ContactGroupResponse])
async def get_contact_groups(
    include_members: bool = Query(False, description="是否包含成员信息"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取联系人分组"""
    contact_service = ContactService(db)
    
    try:
        result = await contact_service.get_contact_groups(
            user_id=current_user.id,
            include_members=include_members
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取分组列表失败")


@router.post("/groups", response_model=ContactGroupResponse)
async def create_contact_group(
    group_data: CreateContactGroupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建联系人分组"""
    contact_service = ContactService(db)
    
    try:
        result = await contact_service.create_contact_group(
            user_id=current_user.id,
            group_data=group_data
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="创建分组失败")


@router.put("/groups/{group_id}", response_model=ContactGroupResponse)
async def update_contact_group(
    group_id: str,
    update_data: UpdateContactGroupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新联系人分组"""
    contact_service = ContactService(db)
    
    try:
        result = await contact_service.update_contact_group(
            user_id=current_user.id,
            group_id=group_id,
            update_data=update_data.dict(exclude_unset=True)
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="更新分组失败")


@router.delete("/groups/{group_id}")
async def delete_contact_group(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除联系人分组"""
    contact_service = ContactService(db)
    
    try:
        await contact_service.delete_contact_group(
            user_id=current_user.id,
            group_id=group_id
        )
        return {"message": "分组删除成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="删除分组失败")


@router.get("/groups/{group_id}/members", response_model=PaginatedGroupMembersResponse)
async def get_group_members(
    group_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取分组成员"""
    contact_service = ContactService(db)
    
    try:
        result = await contact_service.get_group_members(
            user_id=current_user.id,
            group_id=group_id,
            page=page,
            size=size
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取分组成员失败")


@router.put("/groups/{group_id}/members")
async def update_group_members(
    group_id: str,
    member_update: UpdateGroupMembersRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新分组成员"""
    contact_service = ContactService(db)
    
    try:
        await contact_service.update_group_members(
            user_id=current_user.id,
            group_id=group_id,
            add_friendship_ids=member_update.add_friendship_ids,
            remove_friendship_ids=member_update.remove_friendship_ids
        )
        return {"message": "分组成员更新成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="更新分组成员失败")


@router.post("/groups/{group_id}/chat")
async def create_group_chat(
    group_id: str,
    chat_config: CreateGroupChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """基于分组创建群聊"""
    contact_service = ContactService(db)
    
    try:
        result = await contact_service.create_group_chat(
            user_id=current_user.id,
            group_id=group_id,
            title=chat_config.title,
            include_all_members=chat_config.include_all_members,
            member_ids=chat_config.member_ids,
            initial_message=chat_config.initial_message
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="创建群聊失败")


# ============================================================================
# 隐私设置相关API
# ============================================================================

@router.get("/privacy", response_model=ContactPrivacyResponse)
async def get_privacy_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取联系人隐私设置"""
    contact_service = ContactService(db)
    
    try:
        result = await contact_service.get_privacy_settings(user_id=current_user.id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取隐私设置失败")


@router.put("/privacy", response_model=ContactPrivacyResponse)
async def update_privacy_settings(
    settings: UpdatePrivacySettingsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新联系人隐私设置"""
    contact_service = ContactService(db)
    
    try:
        result = await contact_service.update_privacy_settings(
            user_id=current_user.id,
            settings_data=settings.dict()
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="更新隐私设置失败")


# ============================================================================
# 统计分析相关API
# ============================================================================

@router.get("/analytics", response_model=ContactAnalyticsResponse)
async def get_contact_analytics(
    period: str = Query("month", description="统计周期：week/month/quarter/year"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取联系人使用统计"""
    contact_service = ContactService(db)
    
    try:
        result = await contact_service.get_contact_analytics(
            user_id=current_user.id,
            period=period
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取统计数据失败")


# ============================================================================
# 会话集成相关API
# ============================================================================

@router.post("/friends/{friend_id}/conversation")
async def get_or_create_friend_conversation(
    friend_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取或创建与好友的单聊会话"""
    conversation_service = ContactConversationService(db)
    
    try:
        result = await conversation_service.get_or_create_friend_conversation(
            user_id=current_user.id,
            friend_id=friend_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="创建会话失败")


@router.get("/conversations/friends")
async def get_friend_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的所有好友会话"""
    conversation_service = ContactConversationService(db)
    
    try:
        result = await conversation_service.get_friend_conversations(current_user.id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取好友会话失败")
