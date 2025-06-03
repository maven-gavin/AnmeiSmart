"""
聊天API端点 - 重构后的版本，使用分层架构
"""
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, get_current_user
from app.db.models.user import User
from app.db.models.customer import Customer, CustomerProfile
from app.schemas.chat import (
    ConversationCreate, ConversationInfo,
    MessageCreate, MessageCreateRequest, MessageInfo
)
from app.schemas.customer import CustomerProfileInfo, RiskNote, ConsultationHistoryItem

# 导入新的服务层
from app.services.chat import ChatService, MessageService, AIResponseService
from app.services.websocket import websocket_handler, message_broadcaster
from app.core.websocket_manager import websocket_manager
from app.core.events import event_bus, EventTypes

logger = logging.getLogger(__name__)

router = APIRouter()


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
        chat_service = ChatService(db)
        
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
        chat_service = ChatService(db)
        user_role = get_user_role(current_user)
        
        # 如果提供了客户ID且当前用户不是客户本人，检查权限
        if customer_id and current_user.id != customer_id:
            if user_role not in ['consultant', 'doctor', 'admin', 'operator']:
                raise HTTPException(status_code=403, detail="无权访问此客户的会话")
            
            # 验证客户存在
            from app.db.models.user import Role
            customer = db.query(User).join(User.roles).filter(
                User.id == customer_id,
                Role.name == 'customer'
            ).first()
            
            if not customer:
                raise HTTPException(status_code=404, detail="客户不存在")
        
        # 获取会话列表
        if customer_id:
            # 获取指定客户的会话
            from app.db.models.chat import Conversation, Message
            conversations = db.query(Conversation).options(
                joinedload(Conversation.customer)
            ).filter(
                Conversation.customer_id == customer_id
            ).order_by(
                Conversation.updated_at.desc()
            ).offset(skip).limit(limit).all()
            
            # 添加防护代码，确保会话数据格式正确
            result = []
            for conv in conversations:
                # 获取会话的最后一条消息
                last_message = db.query(Message).filter(
                    Message.conversation_id == conv.id
                ).order_by(Message.timestamp.desc()).first()
                
                # 获取发送者信息
                sender_info = None
                if last_message:
                    sender_name = "系统"
                    if last_message.sender_type == "ai":
                        sender_name = "AI助手"
                    elif last_message.sender:
                        sender_name = last_message.sender.username
                    
                    sender_info = {
                        "id": last_message.sender_id or "system",
                        "name": sender_name,
                        "avatar": last_message.sender.avatar if last_message.sender else None,
                        "type": last_message.sender_type
                    }
                
                # 构造规范的会话对象
                conversation_data = {
                    "id": conv.id,
                    "title": conv.title,
                    "customer_id": conv.customer_id,
                    "created_at": conv.created_at,
                    "updated_at": conv.updated_at,
                    "is_active": conv.is_active,
                    "customer": {
                        "id": conv.customer.id,
                        "username": conv.customer.username,
                        "avatar": conv.customer.avatar or '/avatars/user.png'
                    } if conv.customer else None
                }
                
                # 如果有最后一条消息，则添加到返回数据中
                if last_message and sender_info:
                    conversation_data["last_message"] = {
                        "id": last_message.id,
                        "conversation_id": last_message.conversation_id,
                        "content": last_message.content,
                        "type": last_message.type or "text",
                        "sender": sender_info,
                        "timestamp": last_message.timestamp,
                        "is_read": last_message.is_read,
                        "is_important": last_message.is_important
                    }
                else:
                    conversation_data["last_message"] = None
                
                result.append(conversation_data)
            
            return result
        else:
            # 如果没有提供客户ID，则获取当前用户相关的所有会话
            conversations = chat_service.get_conversations(
                user_id=current_user.id,
                user_role=user_role,
                skip=skip,
                limit=limit
            )
            
            return [conversation for conversation in conversations]
        
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
        chat_service = ChatService(db)
        user_role = get_user_role(current_user)
        
        messages = chat_service.get_conversation_messages(
            conversation_id=conversation_id,
            user_id=current_user.id,
            user_role=user_role,
            skip=skip,
            limit=limit
        )
        
        message_service = MessageService(db)
        return [MessageInfo.from_model(msg) for msg in messages]
        
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
    """发送消息（HTTP方式）"""
    try:
        chat_service = ChatService(db)
        user_role = get_user_role(current_user)
        
        message = await chat_service.send_message(
            conversation_id=conversation_id,
            content=message_in.content,
            message_type=message_in.type,
            sender_id=current_user.id,
            sender_type=user_role,
            is_important=False  # 默认值，因为MessageCreate中没有这个字段
        )
        
        message_service = MessageService(db)
        return MessageInfo.from_model(message)
        
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


@router.patch("/conversations/{conversation_id}", response_model=ConversationInfo)
async def update_conversation(
    conversation_id: str,
    update_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新会话信息（如标题）"""
    try:
        chat_service = ChatService(db)
        user_role = get_user_role(current_user)
        
        # 获取原始ORM会话对象（使用内部方法）
        conversation_orm = chat_service._get_conversation_model(
            conversation_id=conversation_id,
            user_id=current_user.id,
            user_role=user_role
        )
        
        if not conversation_orm:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 更新标题
        if 'title' in update_data:
            conversation_orm.title = update_data['title']
            conversation_orm.updated_at = datetime.now()
            db.commit()
            db.refresh(conversation_orm)
        
        # 将ORM对象转换为Pydantic模型
        return ConversationInfo.from_model(conversation_orm)
        
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
    chat_service = ChatService(db)
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
    chat_service = ChatService(db)
    user_role = get_user_role(current_user)
    if user_role not in ["consultant", "doctor", "admin", "operator"]:
        raise HTTPException(status_code=403, detail="无权操作")
    success = chat_service.set_ai_controlled_status(conversation_id, True)
    if not success:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"message": "会话已恢复为AI回复", "is_ai_controlled": True}


# ============ WebSocket 端点 ============

@router.websocket("/ws/{conversation_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    conversation_id: str,
    token: str = Query(...),
    # 添加前端传递的可选参数，避免参数验证失败
    userId: Optional[str] = Query(None),
    userType: Optional[str] = Query(None),
    connectionId: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """WebSocket连接端点 - 简化版，专注于连接管理"""
    connection = None
    user_id = None
    user_role = None
    
    try:
        # 验证token并获取用户信息
        user_info = await verify_websocket_token(token, db)
        if not user_info:
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        user_id = user_info["user_id"]
        user_role = user_info.get("role", "customer")  # 获取用户角色
        
        # 建立WebSocket连接
        connection = await websocket_manager.connect(websocket, user_id, conversation_id)
        
        logger.info(f"WebSocket连接已建立: user_id={user_id}, role={user_role}, conversation_id={conversation_id}")
        
        # 发送连接确认
        await connection.send_json({
            "action": "connected",
            "data": {"conversation_id": conversation_id, "user_role": user_role},
            "timestamp": datetime.now().isoformat()
        })
        
        # 消息处理循环
        while True:
            try:
                # 接收消息
                data = await websocket.receive_json()
                
                # 在消息数据中添加用户角色信息
                if "data" not in data:
                    data["data"] = {}
                data["data"]["sender_type"] = user_role
                
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

async def verify_websocket_token(token: str, db: Session) -> Optional[dict]:
    """验证WebSocket token并返回用户ID和角色"""
    try:
        # 使用安全模块验证token，直接获取user_id
        from app.core.security import verify_token
        user_id = verify_token(token)
        if not user_id:
            logger.warning("WebSocket token验证失败：token无效")
            return None
            
        # 从数据库获取用户信息
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"Token中的用户ID在数据库中不存在: {user_id}")
            return None
        
        # 获取用户当前角色
        user_role = get_user_role(user)
        
        logger.debug(f"WebSocket token验证成功: user_id={user_id}, role={user_role}")
        return {
            "user_id": user_id,
            "role": user_role,
            "username": user.username
        }
        
    except Exception as e:
        logger.error(f"验证WebSocket token失败: {e}")
        return None


def get_user_role_from_token(token: str) -> str:
    """从token中获取用户角色"""
    try:
        from app.core.security import verify_token
        payload = verify_token(token)
        
        if payload and isinstance(payload, dict):
            # 从token payload中获取角色信息
            role = payload.get("role")
            if role:
                return role
            
            # 如果token中没有角色信息，从数据库查询
            user_id = payload.get("sub")
            if user_id:
                # 这里需要访问数据库，但函数签名中没有db参数
                # 简化处理：根据其他信息推断角色
                # 实际项目中应该重构这个函数或改用其他方式
                return "customer"  # 默认角色
        
        return "customer"  # 默认角色
        
    except Exception as e:
        logger.error(f"从token获取角色失败: {e}")
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