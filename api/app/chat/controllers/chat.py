"""
聊天API端点 - 重构后的版本，遵循DDD分层架构
"""
import logging
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.common.deps import get_db
from app.identity_access.deps import get_current_user
from app.identity_access.models.user import User
from app.chat.schemas.chat import (
    ConversationCreate, ConversationInfo,
    MessageCreateRequest, MessageInfo,
    CreateTextMessageRequest, CreateMediaMessageRequest, 
    CreateSystemEventRequest, CreateStructuredMessageRequest
)
from app.core.api import BusinessException

# 导入服务层
from app.chat.services.chat_service import ChatService
from app.chat.deps.chat import get_chat_service

# 导入事件总线
from app.core.websocket.events import event_bus, EventTypes

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ HTTP API 端点 ============

@router.post("/conversations", response_model=ConversationInfo, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_in: ConversationCreate,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """创建新会话"""
    try:
        conversation = chat_service.create_conversation(
            title=conversation_in.title,
            owner_id=str(current_user.id),
            chat_mode=conversation_in.chat_mode or "single",
            tag=conversation_in.tag or "chat"
        )
        return conversation
        
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建会话失败: {e}")
        raise HTTPException(status_code=500, detail="创建会话失败")


@router.get("/conversations", response_model=List[ConversationInfo])
async def get_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """获取会话列表"""
    logger.info(f"端点：开始获取会话列表 - user_id={current_user.id}, skip={skip}, limit={limit}")
    
    try:
        logger.info(f"端点：获取用户角色")
        user_role = chat_service.get_user_role(current_user)
        logger.info(f"端点：用户角色 = {user_role}")
        
        logger.info(f"端点：调用服务获取会话列表")
        conversations = chat_service.get_conversations(
            user_id=str(current_user.id),
            user_role=user_role,
            skip=skip,
            limit=limit
        )
        logger.info(f"端点：成功获取 {len(conversations)} 个会话")
        return conversations
        
    except Exception as e:
        logger.error(f"获取会话列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取会话列表失败")


@router.get("/conversations/{conversation_id}", response_model=ConversationInfo)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """获取指定会话"""
    try:
        conversation = chat_service.get_conversation(
            conversation_id=conversation_id,
            user_id=str(current_user.id)
        )
        
        if not conversation:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return conversation
        
    except HTTPException:
        raise
    except BusinessException as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"获取会话失败: {e}")
        raise HTTPException(status_code=500, detail="获取会话失败")


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageInfo])
async def get_conversation_messages(
    conversation_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """获取会话消息列表"""
    try:
        messages = chat_service.get_conversation_messages(
            conversation_id=conversation_id,
            limit=limit,
            offset=offset
        )
        return messages
        
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取消息列表失败: conversation_id={conversation_id}, error={str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取消息列表失败")


@router.post("/conversations/{conversation_id}/messages", response_model=MessageInfo)
async def create_message(
    conversation_id: str,
    request: MessageCreateRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """创建通用消息"""
    try:
        message = chat_service.create_message_use_case(
            conversation_id=conversation_id,
            request=request,
            sender=current_user
        )
        
        # 广播消息
        await chat_service.broadcast_message_safe(
            conversation_id=conversation_id,
            message_info=message,
            sender_id=str(current_user.id)
        )
        
        return message
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建消息失败")


@router.post("/conversations/{conversation_id}/messages/text", response_model=MessageInfo)
async def create_text_message(
    conversation_id: str,
    request: CreateTextMessageRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """创建文本消息"""
    try:
        message = chat_service.create_text_message_use_case(
            conversation_id=conversation_id,
            request=request,
            sender=current_user
        )
        
        # 广播消息
        await chat_service.broadcast_message_safe(
            conversation_id=conversation_id,
            message_info=message,
            sender_id=str(current_user.id)
        )
        
        return message
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建文本消息失败")


@router.post("/conversations/{conversation_id}/messages/media", response_model=MessageInfo)
async def create_media_message(
    conversation_id: str,
    request: CreateMediaMessageRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """创建媒体消息"""
    try:
        message = chat_service.create_media_message_use_case(
            conversation_id=conversation_id,
            request=request,
            sender=current_user
        )
        
        # 广播消息
        await chat_service.broadcast_message_safe(
            conversation_id=conversation_id,
            message_info=message,
            sender_id=str(current_user.id)
        )
        
        return message
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建媒体消息失败")


@router.post("/conversations/{conversation_id}/messages/system", response_model=MessageInfo)
async def create_system_event_message(
    conversation_id: str,
    request: CreateSystemEventRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """创建系统事件消息"""
    try:
        message = chat_service.create_system_event_message_use_case(
            conversation_id=conversation_id,
            request=request,
            sender=current_user
        )
        
        # 广播消息
        await chat_service.broadcast_message_safe(
            conversation_id=conversation_id,
            message_info=message,
            sender_id=str(current_user.id)
        )
        
        return message
        
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有管理员可以创建系统事件消息")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建系统事件消息失败")


@router.post("/conversations/{conversation_id}/messages/structured", response_model=MessageInfo)
async def create_structured_message(
    conversation_id: str,
    request: CreateStructuredMessageRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """创建结构化消息"""
    try:
        message = chat_service.create_structured_message_use_case(
            conversation_id=conversation_id,
            request=request,
            sender=current_user
        )
        
        # 广播消息
        await chat_service.broadcast_message_safe(
            conversation_id=conversation_id,
            message_info=message,
            sender_id=str(current_user.id)
        )
        
        return message
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建结构化消息失败")



@router.patch("/messages/{message_id}/read")
async def mark_message_as_read(
    message_id: str,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """标记消息为已读"""
    success = chat_service.mark_message_as_read_use_case(message_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="消息不存在")
    
    return {"message": "消息已标记为已读"}


@router.patch("/conversations/{conversation_id}/messages/{message_id}/important")
async def mark_message_as_important(
    conversation_id: str,
    message_id: str,
    request_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """标记消息为重点"""
    try:
        is_important = request_data.get("is_important", False)
        
        success = chat_service.mark_message_as_important_use_case(
            message_id=message_id,
            is_important=is_important
        )
        
        if success:
            return {"message": f"消息已{'标记为重点' if is_important else '取消重点标记'}"}
        else:
            raise HTTPException(status_code=404, detail="消息不存在")
        
    except PermissionError:
        raise HTTPException(status_code=403, detail="无权操作此会话")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"标记消息重点状态失败: {e}")
        raise HTTPException(status_code=500, detail="标记消息重点状态失败")


@router.get("/conversations/{conversation_id}/summary")
async def get_conversation_summary(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """获取会话摘要"""
    try:
        # 暂时返回会话信息作为摘要，后续可以添加专门的摘要功能
        user_role = chat_service.get_user_role(current_user)
        summary = chat_service.get_conversation_by_id_use_case(
            conversation_id=conversation_id,
            user_id=str(current_user.id),
            user_role=user_role
        )
        
        if not summary:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return summary
        
    except Exception as e:
        logger.error(f"获取会话摘要失败: {e}")
        raise HTTPException(status_code=500, detail="获取会话摘要失败")


@router.patch("/conversations/{conversation_id}", response_model=ConversationInfo)
async def update_conversation(
    conversation_id: str,
    update_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """更新会话信息"""
    try:
        updated_conversation = chat_service.update_conversation(
            conversation_id=conversation_id,
            user_id=str(current_user.id),
            updates=update_data
        )
        
        if not updated_conversation:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return updated_conversation
        
    except PermissionError:
        raise HTTPException(status_code=403, detail="无权修改此会话")
    except Exception as e:
        logger.error(f"更新会话失败: {e}")
        raise HTTPException(status_code=500, detail="更新会话失败")


# TODO: 这些功能需要后续实现
# @router.post("/conversations/{conversation_id}/takeover")
# async def consultant_takeover_conversation(
#     conversation_id: str,
#     current_user: User = Depends(get_current_user),
#     chat_app_service: ChatApplicationService = Depends(get_chat_application_service)
# ):
#     """顾问接管会话 - 表现层只负责请求路由和响应格式化"""
#     # TODO: 实现顾问接管会话功能
#     pass

# @router.post("/conversations/{conversation_id}/release")
# async def consultant_release_conversation(
#     conversation_id: str,
#     current_user: User = Depends(get_current_user),
#     chat_app_service: ChatApplicationService = Depends(get_chat_application_service)
# ):
#     """顾问释放会话 - 表现层只负责请求路由和响应格式化"""
#     # TODO: 实现顾问释放会话功能
#     pass


# ============ 事件处理器注册 ============

# 在模块加载时注册事件处理器
def setup_chat_event_handlers():
    """设置聊天相关的事件处理器"""
    
    async def handle_message_sent(event):
        """处理消息发送事件"""
        # 这里可以添加额外的业务逻辑
        # 例如：记录日志、发送通知等
        logger.info(f"消息已发送: conversation_id={event.conversation_id}")
    
    async def handle_ai_response(event):
        """处理AI回复事件"""
        logger.info(f"AI回复已生成: conversation_id={event.conversation_id}")
    
    # 注册事件处理器
    event_bus.subscribe_async(EventTypes.CHAT_MESSAGE_SENT, handle_message_sent)
    event_bus.subscribe_async(EventTypes.AI_RESPONSE_GENERATED, handle_ai_response)


# 初始化事件处理器
setup_chat_event_handlers() 