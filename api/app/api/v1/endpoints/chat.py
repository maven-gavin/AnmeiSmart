"""
聊天API端点 - 重构后的版本，使用分层架构
"""
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.db.models.user import User
from app.schemas.chat import (
    ConversationCreate, ConversationInfo,
    MessageCreate, MessageInfo
)

# 导入新的服务层
from app.services.chat import ChatService, MessageService, AIResponseService
from app.services.websocket import websocket_handler, message_broadcaster
from app.core.websocket_manager import websocket_manager
from app.core.events import event_bus, EventTypes

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ HTTP API 端点 ============

@router.post("/conversations", response_model=ConversationInfo, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_in: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新会话"""
    try:
        chat_service = ChatService(db)
        
        conversation = await chat_service.create_conversation(
            title=conversation_in.title,
            customer_id=conversation_in.customer_id,
            creator_id=current_user.id
        )
        
        return chat_service.convert_conversation_to_schema(conversation)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建会话失败: {e}")
        raise HTTPException(status_code=500, detail="创建会话失败")


@router.get("/conversations", response_model=List[ConversationInfo])
async def get_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取会话列表"""
    try:
        chat_service = ChatService(db)
        user_role = getattr(current_user, 'role', 'customer')
        
        conversations = chat_service.get_conversations(
            user_id=current_user.id,
            user_role=user_role,
            skip=skip,
            limit=limit
        )
        
        return [chat_service.convert_conversation_to_schema(conv) for conv in conversations]
        
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
        chat_service = ChatService(db)
        user_role = getattr(current_user, 'role', 'customer')
        
        conversation = chat_service.get_conversation_by_id(
            conversation_id=conversation_id,
            user_id=current_user.id,
            user_role=user_role
        )
        
        if not conversation:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return chat_service.convert_conversation_to_schema(conversation)
        
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
        chat_service = ChatService(db)
        user_role = getattr(current_user, 'role', 'customer')
        
        messages = chat_service.get_conversation_messages(
            conversation_id=conversation_id,
            user_id=current_user.id,
            user_role=user_role,
            skip=skip,
            limit=limit
        )
        
        message_service = MessageService(db)
        return [message_service.convert_to_schema(msg) for msg in messages]
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取消息失败: {e}")
        raise HTTPException(status_code=500, detail="获取消息失败")


@router.post("/conversations/{conversation_id}/messages", response_model=MessageInfo)
async def send_message(
    conversation_id: str,
    message_in: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """发送消息（HTTP方式）"""
    try:
        chat_service = ChatService(db)
        user_role = getattr(current_user, 'role', 'customer')
        
        message = await chat_service.send_message(
            conversation_id=conversation_id,
            content=message_in.content,
            message_type=message_in.type,
            sender_id=current_user.id,
            sender_type=user_role,
            is_important=False  # 默认值，因为MessageCreate中没有这个字段
        )
        
        message_service = MessageService(db)
        return message_service.convert_to_schema(message)
        
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
        chat_service = ChatService(db)
        updated_count = chat_service.mark_messages_as_read([message_id], current_user.id)
        
        return {"message": f"已标记 {updated_count} 条消息为已读"}
        
    except Exception as e:
        logger.error(f"标记消息已读失败: {e}")
        raise HTTPException(status_code=500, detail="标记消息已读失败")


@router.get("/conversations/{conversation_id}/summary")
async def get_conversation_summary(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取会话摘要"""
    try:
        chat_service = ChatService(db)
        summary = chat_service.get_conversation_summary(conversation_id)
        
        if not summary:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return summary
        
    except Exception as e:
        logger.error(f"获取会话摘要失败: {e}")
        raise HTTPException(status_code=500, detail="获取会话摘要失败")


# ============ WebSocket 端点 ============

@router.websocket("/ws/{conversation_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    conversation_id: str,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """WebSocket连接端点 - 简化版，专注于连接管理"""
    connection = None
    user_id = None
    
    try:
        # 验证token并获取用户信息
        # 这里需要实现token验证逻辑
        user_id = await verify_websocket_token(token, db)
        if not user_id:
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        # 建立WebSocket连接
        connection = await websocket_manager.connect(websocket, user_id, conversation_id)
        
        logger.info(f"WebSocket连接已建立: user_id={user_id}, conversation_id={conversation_id}")
        
        # 发送连接确认
        await connection.send_json({
            "action": "connected",
            "data": {"conversation_id": conversation_id},
            "timestamp": datetime.now().isoformat()
        })
        
        # 消息处理循环
        while True:
            try:
                # 接收消息
                data = await websocket.receive_json()
                
                # 使用WebSocket处理器处理消息
                response = await websocket_handler.handle_websocket_message(
                    data, user_id, conversation_id
                )
                
                # 发送响应（如果需要）
                if response:
                    await connection.send_json(response)
                    
            except WebSocketDisconnect:
                logger.info(f"WebSocket客户端断开连接: user_id={user_id}")
                break
            except json.JSONDecodeError:
                await connection.send_json(
                    websocket_handler.create_error_response("无效的JSON格式")
                )
            except Exception as e:
                logger.error(f"处理WebSocket消息失败: {e}")
                await connection.send_json(
                    websocket_handler.create_error_response(f"处理消息失败: {str(e)}")
                )
    
    except Exception as e:
        logger.error(f"WebSocket连接失败: {e}")
        if websocket.client_state.name != "DISCONNECTED":
            await websocket.close(code=4000, reason="Connection failed")
    
    finally:
        # 清理连接
        if connection and websocket:
            await websocket_manager.disconnect(websocket)


# ============ 辅助函数 ============

async def verify_websocket_token(token: str, db: Session) -> Optional[str]:
    """验证WebSocket token并返回用户ID"""
    try:
        # 这里需要实现实际的token验证逻辑
        # 可以使用JWT或其他认证方式
        # 暂时返回一个示例用户ID
        
        # 示例实现：
        from app.core.security import verify_token
        payload = verify_token(token)
        if payload:
            return payload.get("sub")  # 用户ID
        return None
        
    except Exception as e:
        logger.error(f"验证WebSocket token失败: {e}")
        return None


def get_user_role_from_token(token: str) -> str:
    """从token中获取用户角色"""
    try:
        # 这里需要实现实际的角色获取逻辑
        return "customer"  # 默认角色
    except Exception:
        return "customer"


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

# 确保消息广播器已初始化
_ = message_broadcaster 