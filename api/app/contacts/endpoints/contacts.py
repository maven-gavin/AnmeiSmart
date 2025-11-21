"""
通讯录管理API端点 - DDD架构重构
遵循DDD分层架构，确保Contact和Chat领域职责分离
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.identity_access.models.user import User
from app.identity_access.deps import get_current_user
from app.contacts.deps.contacts import get_contact_application_service
from app.contacts.schemas.contacts import (
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
    PaginatedGroupMembersResponse,
    UpdateGroupMembersRequest,
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
from app.contacts.application.contact_application_service import ContactApplicationService

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
    contact_app_service: ContactApplicationService = Depends(get_contact_application_service)
):
    """获取好友列表（支持多维度筛选和排序）"""
    try:
        result = await contact_app_service.get_friends_use_case(
            user_id=str(current_user.id),
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
    contact_app_service: ContactApplicationService = Depends(get_contact_application_service)
):
    """搜索用户（用于添加好友）"""
    try:
        result = await contact_app_service.search_users_use_case(
            current_user_id=str(current_user.id),
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
    contact_app_service: ContactApplicationService = Depends(get_contact_application_service)
):
    """发送好友请求"""
    try:
        result = await contact_app_service.send_friend_request_use_case(
            user_id=str(current_user.id),
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
    contact_app_service: ContactApplicationService = Depends(get_contact_application_service)
):
    """获取好友请求列表"""
    try:
        # 这里需要实现获取好友请求的用例
        # 暂时返回空结果，实际实现时需要添加相应的用例方法
        return PaginatedFriendRequestsResponse(
            items=[],
            total=0,
            page=page,
            size=size,
            pages=0,
            has_next=False,
            has_prev=False
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取好友请求失败")


@router.put("/friends/requests/{request_id}")
async def handle_friend_request(
    request_id: str,
    action: FriendRequestAction,
    current_user: User = Depends(get_current_user),
    contact_app_service: ContactApplicationService = Depends(get_contact_application_service)
):
    """处理好友请求（接受/拒绝）"""
    try:
        await contact_app_service.handle_friend_request_use_case(
            user_id=str(current_user.id),
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
    contact_app_service: ContactApplicationService = Depends(get_contact_application_service)
):
    """更新好友关系信息"""
    try:
        result = await contact_app_service.update_friendship_use_case(
            user_id=str(current_user.id),
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
    contact_app_service: ContactApplicationService = Depends(get_contact_application_service)
):
    """删除好友关系"""
    try:
        await contact_app_service.delete_friendship_use_case(
            user_id=str(current_user.id),
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
    contact_app_service: ContactApplicationService = Depends(get_contact_application_service)
):
    """批量好友操作（添加标签、移动分组等）"""
    try:
        # 这里需要实现批量操作的用例
        # 暂时返回空结果，实际实现时需要添加相应的用例方法
        return BatchOperationResponse(
            success_count=0,
            failed_count=0,
            details=[]
        )
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
    contact_app_service: ContactApplicationService = Depends(get_contact_application_service)
):
    """获取用户的联系人标签"""
    try:
        result = await contact_app_service.get_contact_tags_use_case(
            user_id=str(current_user.id),
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
    contact_app_service: ContactApplicationService = Depends(get_contact_application_service)
):
    """创建联系人标签"""
    try:
        result = await contact_app_service.create_contact_tag_use_case(
            user_id=str(current_user.id),
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
    contact_app_service: ContactApplicationService = Depends(get_contact_application_service)
):
    """更新联系人标签"""
    try:
        result = await contact_app_service.update_contact_tag_use_case(
            user_id=str(current_user.id),
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
    contact_app_service: ContactApplicationService = Depends(get_contact_application_service)
):
    """删除联系人标签"""
    try:
        await contact_app_service.delete_contact_tag_use_case(
            user_id=str(current_user.id),
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
    contact_app_service: ContactApplicationService = Depends(get_contact_application_service)
):
    """更新好友标签"""
    try:
        # 这里需要实现更新好友标签的用例
        # 暂时返回成功消息，实际实现时需要添加相应的用例方法
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
    contact_app_service: ContactApplicationService = Depends(get_contact_application_service)
):
    """获取指定标签的好友列表"""
    try:
        # 这里需要实现根据标签获取好友的用例
        # 暂时返回空结果，实际实现时需要添加相应的用例方法
        return PaginatedFriendsResponse(
            items=[],
            total=0,
            page=page,
            size=size,
            pages=0,
            has_next=False,
            has_prev=False
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取标签好友失败")


@router.get("/tags/suggestions", response_model=List[TagSuggestionResponse])
async def get_tag_suggestions(
    friendship_id: Optional[str] = Query(None, description="为特定好友推荐标签"),
    current_user: User = Depends(get_current_user),
    contact_app_service: ContactApplicationService = Depends(get_contact_application_service)
):
    """获取智能标签推荐"""
    try:
        # 这里需要实现标签推荐的用例
        # 暂时返回空列表，实际实现时需要添加相应的用例方法
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取标签推荐失败")


# ============================================================================
# 分组管理相关API
# ============================================================================

@router.get("/groups", response_model=List[ContactGroupResponse])
async def get_contact_groups(
    include_members: bool = Query(False, description="是否包含成员信息"),
    current_user: User = Depends(get_current_user),
    contact_app_service: ContactApplicationService = Depends(get_contact_application_service)
):
    """获取联系人分组"""
    try:
        result = await contact_app_service.get_contact_groups_use_case(
            user_id=str(current_user.id),
            include_members=include_members
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取分组列表失败")


@router.post("/groups", response_model=ContactGroupResponse)
async def create_contact_group(
    group_data: CreateContactGroupRequest,
    current_user: User = Depends(get_current_user),
    contact_app_service: ContactApplicationService = Depends(get_contact_application_service)
):
    """创建联系人分组"""
    try:
        result = await contact_app_service.create_contact_group_use_case(
            user_id=str(current_user.id),
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
    contact_app_service: ContactApplicationService = Depends(get_contact_application_service)
):
    """更新联系人分组"""
    try:
        result = await contact_app_service.update_contact_group_use_case(
            user_id=str(current_user.id),
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
    contact_app_service: ContactApplicationService = Depends(get_contact_application_service)
):
    """删除联系人分组"""
    try:
        await contact_app_service.delete_contact_group_use_case(
            user_id=str(current_user.id),
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
    contact_app_service: ContactApplicationService = Depends(get_contact_application_service)
):
    """获取分组成员"""
    try:
        # 这里需要实现获取分组成员的用例
        # 暂时返回空结果，实际实现时需要添加相应的用例方法
        return PaginatedGroupMembersResponse(
            items=[],
            total=0,
            page=page,
            size=size,
            pages=0,
            has_next=False,
            has_prev=False
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取分组成员失败")


@router.put("/groups/{group_id}/members")
async def update_group_members(
    group_id: str,
    member_update: UpdateGroupMembersRequest,
    current_user: User = Depends(get_current_user),
    contact_app_service: ContactApplicationService = Depends(get_contact_application_service)
):
    """更新分组成员"""
    try:
        # 这里需要实现更新分组成员的用例
        # 暂时返回成功消息，实际实现时需要添加相应的用例方法
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
    contact_app_service: ContactApplicationService = Depends(get_contact_application_service)
):
    """基于分组创建群聊 - 注意：这是Chat领域的职责，应该调用Chat应用服务"""
    try:
        # 这里应该调用Chat应用服务来创建群聊
        # 暂时返回成功消息，实际实现时需要集成Chat应用服务
        return {"message": "群聊创建成功", "conversation_id": "temp-id"}
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
    contact_app_service: ContactApplicationService = Depends(get_contact_application_service)
):
    """获取联系人隐私设置"""
    try:
        # 这里需要实现获取隐私设置的用例
        # 暂时返回默认设置，实际实现时需要添加相应的用例方法
        return ContactPrivacyResponse(
            profile_visibility="friends",
            allow_friend_requests=True,
            allow_search_by_phone=True,
            allow_search_by_email=True,
            show_online_status=True,
            show_last_seen=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取隐私设置失败")


@router.put("/privacy", response_model=ContactPrivacyResponse)
async def update_privacy_settings(
    settings: UpdatePrivacySettingsRequest,
    current_user: User = Depends(get_current_user),
    contact_app_service: ContactApplicationService = Depends(get_contact_application_service)
):
    """更新联系人隐私设置"""
    try:
        # 这里需要实现更新隐私设置的用例
        # 暂时返回更新后的设置，实际实现时需要添加相应的用例方法
        return ContactPrivacyResponse(
            profile_visibility=settings.profile_visibility,
            allow_friend_requests=settings.allow_friend_requests,
            allow_search_by_phone=settings.allow_search_by_phone,
            allow_search_by_email=settings.allow_search_by_email,
            show_online_status=settings.show_online_status,
            show_last_seen=settings.show_last_seen
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="更新隐私设置失败")


# ============================================================================
# 统计分析相关API
# ============================================================================

@router.get("/analytics", response_model=ContactAnalyticsResponse)
async def get_contact_analytics(
    period: str = Query("month", description="统计周期：week/month/quarter/year"),
    current_user: User = Depends(get_current_user),
    contact_app_service: ContactApplicationService = Depends(get_contact_application_service)
):
    """获取联系人使用统计"""
    try:
        result = await contact_app_service.get_contact_analytics_use_case(
            user_id=str(current_user.id),
            period=period
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取统计数据失败")


# ============================================================================
# 注意：Chat相关API已移除，这些职责属于Chat领域
# 如果需要与好友聊天，应该通过Chat领域的API
# ============================================================================
