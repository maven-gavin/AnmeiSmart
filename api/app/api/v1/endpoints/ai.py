"""
AI服务API端点
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import uuid4

from app.db.base import get_db
from app.db.models.user import User
from app.db.models.chat import Conversation, Message
from app.schemas.chat import MessageCreate, Message as MessageSchema
from app.core.security import get_current_user, check_role_permission
from app.services.ai import get_ai_service

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/chat", response_model=MessageSchema)
async def get_ai_response(
    message_data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取AI回复
    """
    # 验证会话存在
    conversation = db.query(Conversation).filter(Conversation.id == message_data.conversation_id).first()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    # 检查用户访问权限
    user_role = getattr(current_user, "_active_role", None)
    
    if user_role == "customer" and conversation.customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此会话"
        )
    
    # 创建用户消息
    user_message = Message(
        id=f"msg_{uuid4().hex}",
        conversation_id=message_data.conversation_id,
        content=message_data.content,
        type=message_data.type,
        sender_id=current_user.id,
        sender_type=user_role or "user"
    )
    
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    # 获取会话历史
    conversation_history = db.query(Message).filter(
        Message.conversation_id == message_data.conversation_id
    ).order_by(Message.timestamp).limit(10).all()
    
    # 将会话历史转换为字典列表
    history_list = []
    for msg in conversation_history:
        history_list.append({
            "content": msg.content,
            "sender_type": msg.sender_type,
            "timestamp": msg.timestamp.isoformat()
        })
    
    # 获取AI服务
    ai_service = get_ai_service()
    
    # 生成AI回复
    ai_response = await ai_service.get_response(message_data.content, history_list)
    
    # 创建AI回复消息
    ai_message = Message(
        id=ai_response["id"],
        conversation_id=message_data.conversation_id,
        content=ai_response["content"],
        type="text",
        sender_id="ai",
        sender_type="ai",
        timestamp=datetime.now()
    )
    
    db.add(ai_message)
    
    # 更新会话最后更新时间
    conversation.updated_at = datetime.now()
    
    db.commit()
    db.refresh(ai_message)
    
    # 如果WebSocket已连接，发送广播消息
    from app.api.v1.endpoints.chat import broadcast_to_conversation, active_connections
    
    if message_data.conversation_id in active_connections:
        await broadcast_to_conversation(message_data.conversation_id, {
            "action": "message",
            "data": {
                "id": ai_message.id,
                "content": ai_message.content,
                "type": ai_message.type,
                "sender_id": ai_message.sender_id,
                "sender_type": ai_message.sender_type,
                "is_read": ai_message.is_read,
                "is_important": ai_message.is_important,
                "timestamp": ai_message.timestamp.isoformat()
            },
            "conversation_id": message_data.conversation_id,
            "timestamp": datetime.now().isoformat()
        })
    
    return ai_message 