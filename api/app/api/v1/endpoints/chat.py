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
    MessageCreateRequest, MessageInfo
)

# 导入新的服务层
from app.services.chat import ChatService
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
            customer_id=conversation_in.customer_id,
            creator_id=current_user.id
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
            customer_id=customer_id,
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
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取会话消息"""
    try:
        chat_service = create_chat_service(db)
        user_role = get_user_role(current_user)
        
        # 直接返回service层结果，无需手动转换
        messages = chat_service.get_conversation_messages(
            conversation_id=conversation_id,
            user_id=current_user.id,
            user_role=user_role,
            skip=skip,
            limit=limit
        )
        
        return messages
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取消息失败: {e}")
        raise HTTPException(status_code=500, detail="获取消息失败")


@router.post("/conversations/{conversation_id}/messages", response_model=MessageInfo)
async def send_message(
    conversation_id: str,
    message_in: MessageCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """发送消息（HTTP方式）- 使用新的分布式广播架构"""
    try:
        # 使用工厂函数创建集成了广播服务的ChatService
        chat_service = create_chat_service(db)
        user_role = get_user_role(current_user)
        
        # 使用新的send_message_and_broadcast方法
        message = await chat_service.send_message_and_broadcast(
            conversation_id=conversation_id,
            content=message_in.content,
            message_type=message_in.type,
            sender_id=current_user.id,
            sender_type=user_role,
            is_important=False  # 默认值，因为MessageCreate中没有这个字段
        )
        
        return message
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"发送消息失败: {e}")
        raise HTTPException(status_code=500, detail="发送消息失败")


@router.put("/messages/{message_id}/read")
async def mark_message_as_read(
    message_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """标记消息为已读"""
    try:
        chat_service = create_chat_service(db)
        updated_count = chat_service.mark_messages_as_read([message_id], current_user.id)
        
        return {"message": f"已标记 {updated_count} 条消息为已读"}
        
    except Exception as e:
        logger.error(f"标记消息已读失败: {e}")
        raise HTTPException(status_code=500, detail="标记消息已读失败")


@router.put("/conversations/{conversation_id}/messages/{message_id}/important")
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