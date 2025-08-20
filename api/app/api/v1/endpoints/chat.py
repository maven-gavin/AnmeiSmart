"""
聊天API端点 - 重构后的版本，使用分层架构
"""
import logging
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.db.models.user import User
from app.schemas.chat import (
    ConversationCreate, ConversationInfo,
    MessageCreateRequest, MessageInfo,
    CreateTextMessageRequest, CreateMediaMessageRequest, 
    CreateSystemEventRequest, CreateStructuredMessageRequest,
    AppointmentCardData
)

# 导入新的服务层
from app.services.chat import ChatService
from app.services.chat.message_service import MessageService
from app.core.events import event_bus, EventTypes

# 导入新的分布式WebSocket组件
from app.services.broadcasting_service import BroadcastingService
from app.api.v1.endpoints.websocket import get_connection_manager

logger = logging.getLogger(__name__)

router = APIRouter()


def create_chat_service(db: Session) -> ChatService:
    """
    创建ChatService实例，集成新的广播服务
    """
    try:
        # 获取分布式连接管理器
        connection_manager = get_connection_manager()
        
        # 创建广播服务
        broadcasting_service = BroadcastingService(connection_manager, db)
        
        # 创建ChatService
        return ChatService(db, broadcasting_service)
    except Exception as e:
        logger.warning(f"创建广播服务失败，使用基础ChatService: {e}")
        # 降级处理：如果无法创建广播服务，返回基础ChatService
        return ChatService(db)


def get_user_role(user: User) -> str:
    """获取用户的当前角色"""
    if hasattr(user, '_active_role') and user._active_role:
        return user._active_role
    elif user.roles:
        return user.roles[0].name
    else:
        return 'customer'  # 默认角色


async def broadcast_message_safe(conversation_id: str, message_info: MessageInfo, sender_id: str, db: Session):
    """安全地广播消息，处理错误"""
    try:
        # TODO: 广播功能临时禁用，需要修复BroadcastingService集成
        logger.info(f"消息已创建但未广播: conversation_id={conversation_id}, message_id={message_info.id}")
        pass
    except Exception as e:
        logger.error(f"广播消息失败: {e}")
        # 不抛出异常，因为消息已经成功创建


# ============ HTTP API 端点 ============

@router.post("/conversations", response_model=ConversationInfo, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_in: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新会话"""
    try:
        chat_service = create_chat_service(db)
        
        conversation = await chat_service.create_conversation(
            title=conversation_in.title,
            owner_id=conversation_in.customer_id
        )
        
        return conversation
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建会话失败: {e}")
        raise HTTPException(status_code=500, detail="创建会话失败")


@router.get("/conversations", response_model=List[ConversationInfo])
async def get_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    customer_id: Optional[str] = Query(None, description="客户ID，用于筛选特定客户的会话"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取会话列表，可选根据客户ID筛选"""
    try:
        chat_service = create_chat_service(db)
        user_role = get_user_role(current_user)
        
        # 权限检查
        if customer_id and current_user.id != customer_id:
            if user_role not in ['consultant', 'doctor', 'admin', 'operator']:
                raise HTTPException(status_code=403, detail="无权访问此客户的会话")
        
        # 调用service层获取会话列表，直接返回结果
        conversations = chat_service.get_conversations(
            user_id=current_user.id,
            user_role=user_role,
            target_user_id=customer_id,
            skip=skip,
            limit=limit
        )
        
        return conversations
        
    except Exception as e:
        logger.error(f"获取会话列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取会话列表失败")


@router.get("/conversations/{conversation_id}", response_model=ConversationInfo)
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定会话"""
    try:
        chat_service = create_chat_service(db)
        user_role = get_user_role(current_user)
        
        conversation = chat_service.get_conversation_by_id(
            conversation_id=conversation_id,
            user_id=current_user.id,
            user_role=user_role
        )
        
        if not conversation:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return conversation
        
    except HTTPException:
        # 重新抛出HTTPException，不要捕获
        raise
    except PermissionError:
        raise HTTPException(status_code=403, detail="无权访问此会话")
    except Exception as e:
        logger.error(f"获取会话失败: {e}")
        raise HTTPException(status_code=500, detail="获取会话失败")


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageInfo])
async def get_conversation_messages(
    conversation_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取会话消息列表
    """
    service = MessageService(db)
    
    try:
        messages = service.get_conversation_messages(
            conversation_id=conversation_id,
            skip=offset,
            limit=limit
        )
        
        return messages
        
    except Exception as e:
        logger.error(f"获取消息列表失败: conversation_id={conversation_id}, error={str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取消息列表失败")


@router.post("/conversations/{conversation_id}/messages", response_model=MessageInfo)
async def create_message(
    conversation_id: str,
    request: MessageCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建通用消息 - 支持所有类型 (text, media, system, structured)
    """
    service = MessageService(db)
    
    try:
        message = service.create_message(
            conversation_id=conversation_id,
            sender_id=current_user.id,
            sender_type=get_user_role(current_user),
            content=request.content,
            message_type=request.type,
            is_important=request.is_important,
            reply_to_message_id=request.reply_to_message_id,
            extra_metadata=request.extra_metadata
        )
        
        # 广播消息
        await broadcast_message_safe(conversation_id, MessageInfo.from_model(message), current_user.id, db)
        
        return MessageInfo.from_model(message)
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建消息失败")


@router.post("/conversations/{conversation_id}/messages/text", response_model=MessageInfo)
async def create_text_message(
    conversation_id: str,
    request: CreateTextMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建文本消息的便利端点
    """
    service = MessageService(db)
    
    try:
        message = service.create_text_message(
            conversation_id=conversation_id,
            sender_id=current_user.id,
            sender_type=get_user_role(current_user),
            text=request.text,
            is_important=request.is_important,
            reply_to_message_id=request.reply_to_message_id
        )
        
        # 广播消息
        await broadcast_message_safe(conversation_id, MessageInfo.from_model(message), current_user.id, db)
        
        return MessageInfo.from_model(message)
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建文本消息失败")


@router.post("/conversations/{conversation_id}/messages/media", response_model=MessageInfo)
async def create_media_message(
    conversation_id: str,
    request: CreateMediaMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建媒体消息的便利端点
    """
    service = MessageService(db)
    
    try:
        message = service.create_media_message(
            conversation_id=conversation_id,
            sender_id=current_user.id,
            sender_type=get_user_role(current_user),
            media_url=request.media_url,
            media_name=request.media_name,
            mime_type=request.mime_type,
            size_bytes=request.size_bytes,
            text=request.text,
            metadata=request.metadata,
            is_important=request.is_important,
            reply_to_message_id=request.reply_to_message_id,
            upload_method=request.upload_method
        )
        
        # 广播消息
        await broadcast_message_safe(conversation_id, MessageInfo.from_model(message), current_user.id, db)
        
        return MessageInfo.from_model(message)
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建媒体消息失败")


@router.post("/conversations/{conversation_id}/messages/system", response_model=MessageInfo)
async def create_system_event_message(
    conversation_id: str,
    request: CreateSystemEventRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建系统事件消息的便利端点 - 仅管理员可用
    """
    # 权限检查：只有管理员或系统用户可以创建系统事件消息
    user_role = get_user_role(current_user)
    if user_role not in ["admin", "system"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以创建系统事件消息"
        )
    
    service = MessageService(db)
    
    try:
        message = service.create_system_event_message(
            conversation_id=conversation_id,
            event_type=request.event_type,
            status=request.status,
            event_data=request.event_data
        )
        
        # 广播消息
        await broadcast_message_safe(conversation_id, MessageInfo.from_model(message), current_user.id, db)
        
        return MessageInfo.from_model(message)
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建系统事件消息失败")


@router.post("/conversations/{conversation_id}/messages/structured", response_model=MessageInfo)
async def create_structured_message(
    conversation_id: str,
    request: CreateStructuredMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建结构化消息的便利端点（卡片式消息）
    """
    service = MessageService(db)
    
    try:
        message = service.create_custom_structured_message(
            conversation_id=conversation_id,
            sender_id=current_user.id,
            sender_type=get_user_role(current_user),
            card_type=request.card_type,
            title=request.title,
            data=request.data,
            subtitle=request.subtitle,
            components=request.components,
            actions=request.actions
        )
        
        # 广播消息
        await broadcast_message_safe(conversation_id, MessageInfo.from_model(message), current_user.id, db)
        
        return MessageInfo.from_model(message)
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建结构化消息失败")


@router.post("/conversations/{conversation_id}/messages/appointment", response_model=MessageInfo)
async def create_appointment_confirmation(
    conversation_id: str,
    appointment_data: AppointmentCardData,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建预约确认卡片消息 - 专门用于预约功能
    """
    # 权限检查：只有顾问、医生可以发送预约确认
    user_role = get_user_role(current_user)
    if user_role not in ["consultant", "doctor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有顾问或医生可以发送预约确认"
        )
    
    service = MessageService(db)
    
    try:
        message = service.create_appointment_card_message(
            conversation_id=conversation_id,
            sender_id=current_user.id,
            sender_type=get_user_role(current_user),
            appointment_data=appointment_data,
            title="预约确认",
            subtitle=f"您的{appointment_data.service_name}预约"
        )
        
        # 广播消息
        await broadcast_message_safe(conversation_id, MessageInfo.from_model(message), current_user.id, db)
        
        return MessageInfo.from_model(message)
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建预约确认失败")


@router.patch("/messages/{message_id}/read")
async def mark_message_as_read(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    标记消息为已读
    """
    service = MessageService(db)
    
    success = service.mark_message_as_read(message_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="消息不存在")
    
    return {"message": "消息已标记为已读"}


@router.patch("/conversations/{conversation_id}/messages/read")
async def mark_conversation_messages_as_read(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    标记会话所有消息为已读
    """
    service = MessageService(db)
    
    updated_count = service.mark_conversation_messages_as_read(
        conversation_id=conversation_id,
        user_id=current_user.id
    )
    
    return {"message": f"已标记 {updated_count} 条消息为已读"}


@router.post("/messages/{message_id}/reactions/{emoji}")
async def add_reaction_to_message(
    message_id: str,
    emoji: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    为消息添加反应
    """
    service = MessageService(db)
    
    success = service.add_reaction_to_message(
        message_id=message_id,
        user_id=current_user.id,
        emoji=emoji
    )
    
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="添加反应失败")
    
    return {"message": "反应添加成功"}


@router.delete("/messages/{message_id}/reactions/{emoji}")
async def remove_reaction_from_message(
    message_id: str,
    emoji: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    移除消息的反应
    """
    service = MessageService(db)
    
    success = service.remove_reaction_from_message(
        message_id=message_id,
        user_id=current_user.id,
        emoji=emoji
    )
    
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="移除反应失败")
    
    return {"message": "反应移除成功"}


@router.patch("/conversations/{conversation_id}/messages/{message_id}/important")
async def mark_message_as_important(
    conversation_id: str,
    message_id: str,
    request_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """标记消息为重点"""
    try:
        chat_service = create_chat_service(db)
        user_role = get_user_role(current_user)
        
        is_important = request_data.get("is_important", False)
        
        success = chat_service.mark_message_as_important(
            conversation_id=conversation_id,
            message_id=message_id,
            is_important=is_important,
            user_id=current_user.id,
            user_role=user_role
        )
        
        if success:
            return {"message": f"消息已{'标记为重点' if is_important else '取消重点标记'}"}
        else:
            raise HTTPException(status_code=404, detail="消息不存在")
        
    except PermissionError:
        raise HTTPException(status_code=403, detail="无权访问此会话")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"标记消息重点状态失败: {e}")
        raise HTTPException(status_code=500, detail="标记消息重点状态失败")


@router.get("/conversations/{conversation_id}/summary")
async def get_conversation_summary(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取会话摘要"""
    try:
        chat_service = create_chat_service(db)
        summary = chat_service.get_conversation_summary(conversation_id)
        
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新会话信息（如标题）"""
    try:
        chat_service = create_chat_service(db)
        user_role = get_user_role(current_user)
        
        # 调用service层更新会话，直接返回结果
        updated_conversation = chat_service.update_conversation(
            conversation_id=conversation_id,
            user_id=current_user.id,
            user_role=user_role,
            update_data=update_data
        )
        
        if not updated_conversation:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return updated_conversation
        
    except PermissionError:
        raise HTTPException(status_code=403, detail="无权修改此会话")
    except Exception as e:
        logger.error(f"更新会话失败: {e}")
        raise HTTPException(status_code=500, detail="更新会话失败")


@router.post("/conversations/{conversation_id}/takeover")
async def consultant_takeover_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """顾问接管会话"""
    chat_service = create_chat_service(db)
    user_role = get_user_role(current_user)
    if user_role not in ["consultant", "doctor", "admin", "operator"]:
        raise HTTPException(status_code=403, detail="无权接管会话")
    success = chat_service.set_ai_controlled_status(conversation_id, False)
    if not success:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"message": "会话已由顾问接管", "is_ai_controlled": False}


@router.post("/conversations/{conversation_id}/release")
async def consultant_release_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """顾问取消接管，恢复AI回复"""
    chat_service = create_chat_service(db)
    user_role = get_user_role(current_user)
    if user_role not in ["consultant", "doctor", "admin", "operator"]:
        raise HTTPException(status_code=403, detail="无权操作")
    success = chat_service.set_ai_controlled_status(conversation_id, True)
    if not success:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"message": "会话已恢复为AI回复", "is_ai_controlled": True}




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