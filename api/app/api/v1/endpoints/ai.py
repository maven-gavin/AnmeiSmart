"""
AI服务API端点
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.base import get_db
from app.db.models.user import User
from app.db.models.chat import Conversation, Message
from app.schemas.chat import MessageCreate, MessageInfo
from app.core.security import get_current_user, check_role_permission
from app.services.ai import get_ai_service
from app.services.chat import ChatService, MessageService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/chat", response_model=MessageInfo)
async def get_ai_response(
    message_data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取AI回复
    """
    try:
        chat_service = ChatService(db)
        message_service = MessageService(db)
        user_role = getattr(current_user, 'role', 'customer')
        
        # 验证会话存在和权限
        conversation = chat_service.get_conversation_by_id(
            message_data.conversation_id,
            current_user.id,
            user_role
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在或无权访问"
            )
        
        # 发送用户消息
        user_message = await chat_service.send_message(
            conversation_id=message_data.conversation_id,
            content=message_data.content,
            message_type=message_data.type,
            sender_id=current_user.id,
            sender_type=user_role
        )
        
        # 获取AI服务
        ai_service = get_ai_service()
        
        # 获取会话历史
        history = message_service.get_recent_messages(message_data.conversation_id, 10)
        history_list = []
        for msg in history:
            history_list.append({
                "content": msg.content,
                "sender_type": msg.sender_type,
                "timestamp": msg.timestamp.isoformat()
            })
        
        # 生成AI回复
        ai_response = await ai_service.get_response(message_data.content, history_list)
        
        # 创建AI回复消息
        ai_message = await message_service.create_message(
            conversation_id=message_data.conversation_id,
            content=ai_response.get("content", "抱歉，我暂时无法回复"),
            message_type="text",
            sender_id="ai",
            sender_type="ai"
        )
        
        # 转换为响应格式
        return message_service.convert_to_schema(ai_message)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"AI回复生成失败: {e}")
        raise HTTPException(status_code=500, detail="生成AI回复时发生错误") 