import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import uuid4

from app.db.base import get_db
from app.db.models.user import User
from app.db.models.chat import Conversation, Message, CustomerProfile
from app.schemas.chat import (
    ConversationCreate, Conversation as ConversationSchema,
    MessageCreate, Message as MessageSchema,
    CustomerProfile as CustomerProfileSchema,
    WebSocketMessage
)
from app.core.security import get_current_user, check_role_permission
from app.services.ai import get_ai_service

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# 存储活跃的WebSocket连接
active_connections: Dict[str, List[WebSocket]] = {}

# 存储用户与会话的关联
user_conversation_mapping: Dict[str, List[str]] = {}


# 辅助函数：广播消息给会话中的所有用户
async def broadcast_to_conversation(conversation_id: str, message: Dict[str, Any]):
    """向会话中的所有连接发送消息"""
    if conversation_id in active_connections:
        disconnected_websockets = []
        for websocket in active_connections[conversation_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                disconnected_websockets.append(websocket)
        
        # 移除断开的连接
        for ws in disconnected_websockets:
            if ws in active_connections[conversation_id]:
                active_connections[conversation_id].remove(ws)


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, token: str = None):
    """WebSocket连接端点"""
    await websocket.accept()
    
    # 验证用户身份（简化版，实际应使用JWT验证）
    if not token:
        await websocket.send_json({
            "action": "error",
            "data": {"message": "未提供认证令牌"}
        })
        await websocket.close()
        return
    
    # 存储用户连接
    # 注意：此处简化处理，实际应该是每个会话一个连接组
    
    try:
        # 等待客户端发送初始连接消息
        connect_data = await websocket.receive_json()
        
        if not isinstance(connect_data, dict) or connect_data.get("action") != "connect":
            await websocket.send_json({
                "action": "error",
                "data": {"message": "无效的连接消息"}
            })
            await websocket.close()
            return
        
        # 获取会话ID
        conversation_id = connect_data.get("conversation_id")
        if not conversation_id:
            await websocket.send_json({
                "action": "error",
                "data": {"message": "未提供会话ID"}
            })
            await websocket.close()
            return
        
        # 将连接添加到会话
        if conversation_id not in active_connections:
            active_connections[conversation_id] = []
        active_connections[conversation_id].append(websocket)
        
        # 将用户与会话关联
        if user_id not in user_conversation_mapping:
            user_conversation_mapping[user_id] = []
        if conversation_id not in user_conversation_mapping[user_id]:
            user_conversation_mapping[user_id].append(conversation_id)
        
        # 发送成功连接消息
        await websocket.send_json({
            "action": "connect",
            "data": {"status": "connected"},
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat()
        })
        
        # 通知其他连接用户有新用户加入
        await broadcast_to_conversation(conversation_id, {
            "action": "system",
            "data": {"message": f"用户 {user_id} 已连接"},
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat()
        })
        
        # 持续接收消息
        while True:
            data = await websocket.receive_json()
            
            # 确保数据是字典
            if not isinstance(data, dict):
                await websocket.send_json({
                    "action": "error",
                    "data": {"message": "无效的消息格式"}
                })
                continue
            
            # 处理不同类型的消息
            action = data.get("action")
            
            if action == "message":
                # 处理消息发送
                message_data = data.get("data", {})
                
                # 创建消息ID
                message_id = f"msg_{uuid4().hex}"
                
                # 构建完整消息
                complete_message = {
                    "action": "message",
                    "data": {
                        "id": message_id,
                        "content": message_data.get("content", ""),
                        "type": message_data.get("type", "text"),
                        "sender_id": user_id,
                        "sender_type": message_data.get("sender_type", "user"),
                        "is_read": False,
                        "is_important": False
                    },
                    "conversation_id": conversation_id,
                    "timestamp": datetime.now().isoformat()
                }
                
                # 广播消息给所有连接的用户
                await broadcast_to_conversation(conversation_id, complete_message)
                
                # 保存消息到数据库
                try:
                    # 创建同步数据库会话
                    from app.db.base import SessionLocal
                    db = SessionLocal()
                    
                    # 验证会话是否存在
                    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
                    if conversation:
                        # 创建新消息
                        new_message = Message(
                            id=message_id,
                            conversation_id=conversation_id,
                            content=message_data.get("content", ""),
                            type=message_data.get("type", "text"),
                            sender_id=user_id,
                            sender_type=message_data.get("sender_type", "user"),
                            is_read=False,
                            is_important=False
                        )
                        
                        db.add(new_message)
                        
                        # 更新会话最后更新时间
                        conversation.updated_at = datetime.now()
                        
                        db.commit()
                        logger.info(f"消息已保存到数据库: {message_id}")
                        
                        # 检查是否需要AI自动回复
                        # 获取AI接管状态（如果AI接管设置为False则由顾问接管）
                        is_ai_controlled = True  # 默认由AI处理
                        
                        # 获取最近的会话历史
                        conversation_history = db.query(Message).filter(
                            Message.conversation_id == conversation_id
                        ).order_by(Message.timestamp.desc()).limit(10).all()
                        
                        # 转换为AI服务需要的格式
                        history_list = []
                        for msg in conversation_history:
                            history_list.append({
                                "content": msg.content,
                                "sender_type": msg.sender_type,
                                "timestamp": msg.timestamp.isoformat()
                            })
                        
                        # 判断是否由AI回复
                        if is_ai_controlled:
                            # 获取AI服务
                            ai_service = get_ai_service()
                            
                            # 生成AI回复
                            ai_response = await ai_service.get_response(
                                message_data.get("content", ""), 
                                history_list
                            )
                            
                            # 创建AI回复消息
                            ai_message = Message(
                                id=ai_response["id"],
                                conversation_id=conversation_id,
                                content=ai_response["content"],
                                type="text",
                                sender_id="ai",
                                sender_type="ai",
                                timestamp=datetime.now()
                            )
                            
                            db.add(ai_message)
                            db.commit()
                            
                            # 广播AI回复消息
                            await broadcast_to_conversation(conversation_id, {
                                "action": "message",
                                "data": {
                                    "id": ai_message.id,
                                    "content": ai_message.content,
                                    "type": ai_message.type,
                                    "sender_id": ai_message.sender_id,
                                    "sender_type": ai_message.sender_type,
                                    "is_read": False,
                                    "is_important": False
                                },
                                "conversation_id": conversation_id,
                                "timestamp": datetime.now().isoformat()
                            })
                            
                            logger.info(f"AI回复已生成并广播: {ai_message.id}")
                        
                    else:
                        logger.error(f"会话不存在: {conversation_id}")
                except Exception as e:
                    logger.error(f"保存消息到数据库时出错: {e}")
                finally:
                    db.close()
                
            elif action == "typing":
                # 处理正在输入状态
                await broadcast_to_conversation(conversation_id, {
                    "action": "typing",
                    "data": {"is_typing": data.get("data", {}).get("is_typing", False)},
                    "sender_id": user_id,
                    "conversation_id": conversation_id,
                    "timestamp": datetime.now().isoformat()
                })
                
            elif action == "read":
                # 处理已读消息
                message_ids = data.get("data", {}).get("message_ids", [])
                
                # 更新数据库中的消息状态
                try:
                    # 创建同步数据库会话
                    from app.db.base import SessionLocal
                    db = SessionLocal()
                    
                    # 更新消息状态
                    for message_id in message_ids:
                        message = db.query(Message).filter(Message.id == message_id).first()
                        if message:
                            message.is_read = True
                    
                    db.commit()
                    logger.info(f"已更新消息已读状态: {message_ids}")
                except Exception as e:
                    logger.error(f"更新消息已读状态时出错: {e}")
                finally:
                    db.close()
                
                # 广播已读状态
                await broadcast_to_conversation(conversation_id, {
                    "action": "read",
                    "data": {"message_ids": message_ids},
                    "sender_id": user_id,
                    "conversation_id": conversation_id,
                    "timestamp": datetime.now().isoformat()
                })
                
            elif action == "disconnect":
                # 用户主动断开连接
                break
            
            else:
                # 未知操作
                await websocket.send_json({
                    "action": "error",
                    "data": {"message": f"未知操作: {action}"}
                })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user: {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # 清理连接
        if conversation_id in active_connections and websocket in active_connections[conversation_id]:
            active_connections[conversation_id].remove(websocket)
            if not active_connections[conversation_id]:
                del active_connections[conversation_id]
                
        # 清理用户会话映射
        if user_id in user_conversation_mapping:
            if conversation_id in user_conversation_mapping[user_id]:
                user_conversation_mapping[user_id].remove(conversation_id)
                if not user_conversation_mapping[user_id]:
                    del user_conversation_mapping[user_id]
        
        logger.info(f"WebSocket connection removed for user: {user_id}")


@router.post("/conversations", response_model=ConversationSchema, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_in: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新会话"""
    # 检查用户权限
    user_role = getattr(current_user, "_active_role", None)
    
    # 验证顾客存在
    customer = db.query(User).filter(User.id == conversation_in.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="顾客不存在"
        )
    
    # 创建会话
    new_conversation = Conversation(
        id=f"conv_{uuid4().hex}",
        title=conversation_in.title,
        customer_id=conversation_in.customer_id
    )
    
    db.add(new_conversation)
    db.commit()
    db.refresh(new_conversation)
    
    # 创建系统消息
    system_message = Message(
        conversation_id=new_conversation.id,
        content="会话已创建",
        type="system",
        sender_id=current_user.id,
        sender_type="system"
    )
    
    db.add(system_message)
    db.commit()
    
    # 构建响应
    return ConversationSchema(
        id=new_conversation.id,
        title=new_conversation.title,
        customer_id=new_conversation.customer_id,
        created_at=new_conversation.created_at,
        updated_at=new_conversation.updated_at,
        is_active=new_conversation.is_active
    )


@router.get("/conversations", response_model=List[ConversationSchema])
async def get_conversations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的所有会话"""
    # 检查用户角色
    user_role = getattr(current_user, "_active_role", None)
    
    if user_role == "customer":
        # 顾客只能看到自己的会话
        query = db.query(Conversation).filter(Conversation.customer_id == current_user.id)
    else:
        # 顾问、医生等可以看到所有会话
        query = db.query(Conversation)
    
    # 分页查询
    conversations = query.offset(skip).limit(limit).all()
    
    return conversations


@router.get("/conversations/{conversation_id}", response_model=ConversationSchema)
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定会话"""
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    # 检查用户角色和访问权限
    user_role = getattr(current_user, "_active_role", None)
    
    if user_role == "customer" and conversation.customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此会话"
        )
    
    return conversation


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageSchema])
async def get_conversation_messages(
    conversation_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取会话消息"""
    # 验证会话存在
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
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
    
    # 获取消息，按时间排序
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.timestamp).offset(skip).limit(limit).all()
    
    return messages


@router.post("/conversations/{conversation_id}/messages", response_model=MessageSchema)
async def create_message(
    conversation_id: str,
    message_in: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新消息"""
    # 验证会话存在
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
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
    
    # 创建新消息
    new_message = Message(
        id=f"msg_{uuid4().hex}",
        conversation_id=conversation_id,
        content=message_in.content,
        type=message_in.type,
        sender_id=current_user.id,
        sender_type=user_role or "system"
    )
    
    db.add(new_message)
    
    # 更新会话最后更新时间
    conversation.updated_at = datetime.now()
    
    db.commit()
    db.refresh(new_message)
    
    # 如果存在WebSocket连接，广播消息
    if conversation_id in active_connections:
        await broadcast_to_conversation(conversation_id, {
            "action": "message",
            "data": {
                "id": new_message.id,
                "content": new_message.content,
                "type": new_message.type,
                "sender_id": new_message.sender_id,
                "sender_type": new_message.sender_type,
                "is_read": new_message.is_read,
                "is_important": new_message.is_important,
                "timestamp": new_message.timestamp.isoformat()
            },
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat()
        })
    
    return new_message 