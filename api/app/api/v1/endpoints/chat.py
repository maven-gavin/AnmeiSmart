import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from uuid import uuid4

from app.db.base import get_db
from app.db.models.user import User
from app.db.models.chat import Conversation, Message, CustomerProfile
from app.schemas.chat import (
    ConversationCreate, Conversation as ConversationSchema,
    MessageCreate, Message as MessageSchema,
    CustomerProfile as CustomerProfileSchema,
    WebSocketMessage, MessageSender
)
from app.core.security import get_current_user, check_role_permission
from app.services.ai import get_ai_service

# 配置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# 设置更详细的日志级别
logger.setLevel(logging.DEBUG)

router = APIRouter()

# 存储活跃的WebSocket连接
active_connections: Dict[str, List[WebSocket]] = {}

# 存储用户与会话的关联
user_conversation_mapping: Dict[str, List[str]] = {}


# 辅助函数：广播消息给会话中的所有用户
async def broadcast_to_conversation(conversation_id: str, message: Dict[str, Any]):
    """向会话中的所有连接发送消息"""
    if conversation_id in active_connections:
        logger.info(f"广播消息到会话 {conversation_id}, 当前连接数: {len(active_connections[conversation_id])}")
        logger.info(f"消息类型: {message.get('action')}, 发送者: {message.get('sender_id', '未知')}")
        
        # 获取会话相关用户列表以便调试
        user_ids = []
        for ws in active_connections[conversation_id]:
            user_id = getattr(ws, "user_id", "unknown")
            user_ids.append(user_id)
        
        logger.info(f"会话 {conversation_id} 的连接用户: {user_ids}")
        
        disconnected_websockets = []
        for websocket in active_connections[conversation_id]:
            try:
                await websocket.send_json(message)
                logger.debug(f"消息已发送到用户: {getattr(websocket, 'user_id', 'unknown')}")
            except Exception as e:
                logger.error(f"广播消息失败: {e}, 用户: {getattr(websocket, 'user_id', 'unknown')}")
                disconnected_websockets.append(websocket)
        
        # 移除断开的连接
        for ws in disconnected_websockets:
            if ws in active_connections[conversation_id]:
                logger.info(f"移除断开的连接: 用户={getattr(ws, 'user_id', 'unknown')}")
                active_connections[conversation_id].remove(ws)
    else:
        logger.warning(f"尝试广播到不存在的会话: {conversation_id}")


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, token: str = None):
    """WebSocket连接端点"""
    logger.info(f"新的WebSocket连接请求: user_id={user_id}")
    
    # 将用户ID存储到WebSocket对象，便于后续识别
    websocket.user_id = user_id
    
    try:
        await websocket.accept()
        logger.info(f"WebSocket连接已接受: user_id={user_id}")
        
        # 验证用户身份（简化版，实际应使用JWT验证）
        if not token:
            logger.warning(f"WebSocket连接未提供认证令牌: user_id={user_id}")
            await websocket.send_json({
                "action": "error",
                "data": {"message": "未提供认证令牌"}
            })
            await websocket.close()
            return
        
        try:
            # 等待客户端发送初始连接消息
            logger.info(f"等待客户端初始连接消息: user_id={user_id}")
            connect_data = await websocket.receive_json()
            logger.info(f"收到初始连接消息: {connect_data}")
            
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
            
            # 在添加到active_connections前记录日志
            logger.info(f"将用户 {user_id} 添加到会话 {conversation_id} 的连接列表")
            logger.info(f"当前会话 {conversation_id} 的连接数: {len(active_connections.get(conversation_id, []))}")
            
            # 将连接添加到会话
            if conversation_id not in active_connections:
                active_connections[conversation_id] = []
            active_connections[conversation_id].append(websocket)
            
            logger.info(f"添加后会话 {conversation_id} 的连接数: {len(active_connections[conversation_id])}")
            
            # 记录当前所有会话和连接情况
            all_sessions = {cid: len(conns) for cid, conns in active_connections.items()}
            logger.info(f"当前所有活跃会话连接: {all_sessions}")
            
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
                try:
                    data = await websocket.receive_json()
                    logger.info(f"收到WebSocket消息: {data}")
                    
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
                                    
                                    try:
                                        # 设置超时限制
                                        import asyncio
                                        from asyncio import TimeoutError
                                        
                                        # 生成AI回复，设置10秒超时
                                        ai_response = await asyncio.wait_for(
                                            ai_service.get_response(
                                                message_data.get("content", ""), 
                                                history_list
                                            ),
                                            timeout=10.0
                                        )
                                        
                                        # 创建AI回复消息
                                        ai_message_id = f"msg_{uuid4().hex}"
                                        ai_message = Message(
                                            id=ai_message_id,
                                            conversation_id=conversation_id,
                                            content=ai_response.get("content", "暂无回复"),
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
                                    
                                    except TimeoutError:
                                        # 处理超时异常
                                        logger.error("AI响应生成超时")
                                        
                                        # 创建超时错误消息
                                        timeout_message = Message(
                                            id=f"msg_{uuid4().hex}",
                                            conversation_id=conversation_id,
                                            content="AI响应超时，请稍后再试",
                                            type="text",
                                            sender_id="system",
                                            sender_type="system",
                                            timestamp=datetime.now(),
                                            is_system=True
                                        )
                                        
                                        db.add(timeout_message)
                                        db.commit()
                                        
                                        # 广播超时消息
                                        await broadcast_to_conversation(conversation_id, {
                                            "action": "system",
                                            "data": {
                                                "id": timeout_message.id,
                                                "content": timeout_message.content,
                                                "type": timeout_message.type,
                                                "sender_id": timeout_message.sender_id,
                                                "sender_type": timeout_message.sender_type,
                                                "is_read": False,
                                                "is_important": False,
                                                "is_system": True
                                            },
                                            "conversation_id": conversation_id,
                                            "timestamp": datetime.now().isoformat()
                                        })
                                    
                                    except Exception as e:
                                        # 处理其他异常
                                        logger.error(f"生成AI回复时出错: {str(e)}")
                                        
                                        # 创建错误消息
                                        error_message = Message(
                                            id=f"msg_{uuid4().hex}",
                                            conversation_id=conversation_id,
                                            content=f"生成回复时出错: {str(e)}",
                                            type="text",
                                            sender_id="system",
                                            sender_type="system",
                                            timestamp=datetime.now(),
                                            is_system=True
                                        )
                                        
                                        db.add(error_message)
                                        db.commit()
                                        
                                        # 广播错误消息
                                        await broadcast_to_conversation(conversation_id, {
                                            "action": "system",
                                            "data": {
                                                "id": error_message.id,
                                                "content": error_message.content,
                                                "type": error_message.type,
                                                "sender_id": error_message.sender_id,
                                                "sender_type": error_message.sender_type,
                                                "is_read": False,
                                                "is_important": False,
                                                "is_system": True
                                            },
                                            "conversation_id": conversation_id,
                                            "timestamp": datetime.now().isoformat()
                                        })
                                
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
                    
                    elif action == "ping":
                        # 处理心跳消息
                        logger.debug(f"收到心跳消息: user_id={user_id}, conversation_id={conversation_id}")
                        await websocket.send_json({
                            "action": "pong",
                            "timestamp": datetime.now().isoformat()
                        })
                    
                    else:
                        # 未知操作
                        await websocket.send_json({
                            "action": "error",
                            "data": {"message": f"未知操作: {action}"}
                        })
                except WebSocketDisconnect:
                    logger.info(f"WebSocket连接断开: user_id={user_id}, conversation_id={conversation_id}")
                    break
                except json.JSONDecodeError:
                    logger.error(f"无效的JSON数据: user_id={user_id}")
                    await websocket.send_json({
                        "action": "error",
                        "data": {"message": "无效的JSON数据"}
                    })
                except Exception as e:
                    logger.error(f"处理WebSocket消息时出错: {str(e)}")
                    await websocket.send_json({
                        "action": "error",
                        "data": {"message": f"处理消息时出错: {str(e)}"}
                    })
        except WebSocketDisconnect:
            logger.info(f"WebSocket连接在初始化阶段断开: user_id={user_id}")
        except json.JSONDecodeError:
            logger.error(f"初始化阶段收到无效的JSON数据: user_id={user_id}")
            await websocket.send_json({
                "action": "error",
                "data": {"message": "无效的JSON数据"}
            })
        except Exception as e:
            logger.error(f"WebSocket处理时出错: {str(e)}")
            try:
                await websocket.send_json({
                    "action": "error",
                    "data": {"message": f"服务器错误: {str(e)}"}
                })
            except:
                logger.error("无法发送错误消息到WebSocket")
        finally:
            # 清理连接
            try:
                # 从活动连接中移除
                if 'conversation_id' in locals() and conversation_id in active_connections:
                    if websocket in active_connections[conversation_id]:
                        active_connections[conversation_id].remove(websocket)
                    
                    # 如果会话没有活动连接，则删除会话记录
                    if not active_connections[conversation_id]:
                        del active_connections[conversation_id]
                
                # 从用户会话映射中移除
                if user_id in user_conversation_mapping and 'conversation_id' in locals():
                    if conversation_id in user_conversation_mapping[user_id]:
                        user_conversation_mapping[user_id].remove(conversation_id)
                    
                    # 如果用户没有活动会话，则删除用户记录
                    if not user_conversation_mapping[user_id]:
                        del user_conversation_mapping[user_id]
                
                # 通知其他用户有用户离开
                if 'conversation_id' in locals() and conversation_id in active_connections:
                    await broadcast_to_conversation(conversation_id, {
                        "action": "system",
                        "data": {"message": f"用户 {user_id} 已断开连接"},
                        "conversation_id": conversation_id,
                        "timestamp": datetime.now().isoformat()
                    })
            except Exception as e:
                logger.error(f"清理WebSocket连接时出错: {str(e)}")
    except Exception as e:
        logger.error(f"WebSocket连接初始化失败: {str(e)}")
        try:
            await websocket.close()
        except:
            pass


@router.post("/conversations", response_model=ConversationSchema, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_in: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新会话"""
    # 检查用户权限
    user_role = getattr(current_user, "_active_role", None)
    logger.info(f"尝试创建会话: 用户={current_user.id}, 角色={user_role}")
    
    # 支持通过email或customer_id查找客户
    customer = None
    customer_id = conversation_in.customer_id
    customer_email = getattr(conversation_in, "customer_email", None)
    
    if not customer_id and customer_email:
        # 通过邮箱查找客户
        logger.info(f"通过邮箱查找客户: {customer_email}")
        customer = db.query(User).filter(User.email == customer_email).first()
        if customer:
            customer_id = customer.id
    
    if customer_id:
        # 通过ID查找客户
        logger.info(f"通过ID查找客户: {customer_id}")
        customer = db.query(User).filter(User.id == customer_id).first()
    
    if not customer:
        # 对于测试环境，如果找不到客户，创建一个默认客户
        if customer_email and 'example.com' in customer_email:
            logger.info(f"创建测试客户: {customer_email}")
            # 创建测试客户 (仅用于测试)
            customer = User(
                email=customer_email,
                name="测试客户",
                _active_role="customer"
            )
            db.add(customer)
            db.commit()
            db.refresh(customer)
            customer_id = customer.id
        else:
            logger.error(f"客户不存在: id={customer_id}, email={customer_email}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="客户不存在"
            )
    
    # 创建会话，使用UUID作为ID以避免冲突
    new_conversation = Conversation(
        id=f"conv_{uuid4().hex}",
        title=conversation_in.title or f"会话 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        customer_id=customer_id
    )
    
    db.add(new_conversation)
    db.commit()
    db.refresh(new_conversation)
    
    logger.info(f"会话创建成功: id={new_conversation.id}")
    
    # 创建系统消息
    system_message = Message(
        id=f"msg_{uuid4().hex}",
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
    logger.info(f"获取用户会话列表: user_id={current_user.id}, email={current_user.email}")
    
    # 检查用户角色
    user_role = getattr(current_user, "_active_role", None)
    user_roles = [role.name for role in current_user.roles] if current_user.roles else []
    
    logger.debug(f"用户角色: 活跃角色={user_role}, 所有角色={user_roles}")
    
    # 根据角色过滤会话
    if user_role == "customer":
        # 客户只能看到自己的会话
        conversations = db.query(Conversation).filter(
            Conversation.customer_id == current_user.id
        ).options(
            joinedload(Conversation.customer)  # 确保预加载客户信息
        ).order_by(Conversation.updated_at.desc()).offset(skip).limit(limit).all()
    elif user_role in ["consultant", "doctor", "admin", "operator"]:
        # 顾问、医生、管理员可以看到所有会话
        conversations = db.query(Conversation).options(
            joinedload(Conversation.customer)  # 确保预加载客户信息
        ).order_by(
            Conversation.updated_at.desc()
        ).offset(skip).limit(limit).all()
    else:
        # 未知角色
        logger.warning(f"未知用户角色: {user_role}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问会话列表"
        )
    
    logger.info(f"查询结果: 找到 {len(conversations)} 个会话")
    
    # 使用辅助函数构建响应
    result_conversations = []
    for conversation in conversations:
        # 确保客户信息存在
        if conversation.customer_id and not conversation.customer:
            logger.warning(f"会话 {conversation.id} 的客户信息未预加载，尝试手动加载")
            conversation.customer = db.query(User).filter(User.id == conversation.customer_id).first()
        
        conv_data = convert_conversation_to_schema(conversation, db)
        # 记录最终转换后的数据，以便调试
        logger.debug(f"转换后的会话数据: {conv_data}")
        
        # 确保customer字段存在于结果中
        if "customer" not in conv_data and conversation.customer:
            logger.warning(f"会话 {conversation.id} 转换后缺少customer字段，手动添加")
            conv_data["customer"] = {
                "id": conversation.customer.id,
                "username": conversation.customer.username,
                "email": conversation.customer.email,
                "avatar": conversation.customer.avatar
            }
        
        result_conversations.append(conv_data)
    
    # 打印最终响应前的数据
    logger.info(f"即将返回会话列表，数据示例: {result_conversations[0] if result_conversations else 'None'}")
    
    return result_conversations


@router.get("/conversations/{conversation_id}", response_model=ConversationSchema)
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定会话"""
    logger.info(f"获取会话详情: conversation_id={conversation_id}, user_id={current_user.id}, email={current_user.email}")
    
    # 验证会话存在
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        logger.warning(f"会话不存在: conversation_id={conversation_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    # 检查用户权限
    user_role = getattr(current_user, "_active_role", None)
    if user_role == "customer" and conversation.customer_id != current_user.id:
        logger.warning(f"访问权限不足: user_id={current_user.id}, role={user_role}, 会话所属客户={conversation.customer_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此会话"
        )
    
    # 获取会话最后一条消息
    last_message = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.timestamp.desc()).first()
    
    # 使用辅助函数构建API响应格式
    response = convert_conversation_to_schema(conversation, db)
    
    logger.info(f"访问会话成功: conversation_id={conversation_id}")
    return response


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageSchema])
async def get_conversation_messages(
    conversation_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取会话消息"""
    logger.info(f"获取会话消息: conversation_id={conversation_id}, user_id={current_user.id}, email={current_user.email}")
    
    # 验证会话存在
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        logger.warning(f"会话不存在: conversation_id={conversation_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    # 检查用户访问权限
    user_role = getattr(current_user, "_active_role", None)
    user_roles = [role.name for role in current_user.roles] if current_user.roles else []
    logger.debug(f"用户角色: 活跃角色={user_role}, 所有角色={user_roles}, 会话所属客户: {conversation.customer_id}")
    
    if user_role == "customer" and conversation.customer_id != current_user.id:
        logger.warning(f"访问权限不足: user_id={current_user.id}, role={user_role}, 尝试访问会话 {conversation_id}，但该会话属于客户 {conversation.customer_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此会话"
        )
    
    # 获取消息，按时间排序
    logger.debug(f"查询会话消息: conversation_id={conversation_id}, skip={skip}, limit={limit}")
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.timestamp).offset(skip).limit(limit).all()
    
    logger.info(f"查询结果: 找到 {len(messages)} 条消息")
    
    # 使用辅助函数转换消息格式
    result_messages = []
    for message in messages:
        # 转换消息为API响应格式
        message_dict = convert_message_to_schema(message)
        result_messages.append(message_dict)
    
    return result_messages


@router.post("/conversations/{conversation_id}/messages", response_model=MessageSchema)
async def create_message(
    conversation_id: str,
    message_in: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新消息"""
    logger.info(f"创建新消息: conversation_id={conversation_id}, user_id={current_user.id}, email={current_user.email}")
    
    # 验证会话存在
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        logger.warning(f"会话不存在: conversation_id={conversation_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    # 检查用户权限
    user_role = getattr(current_user, "_active_role", None)
    if user_role == "customer" and conversation.customer_id != current_user.id:
        logger.warning(f"权限不足: user_id={current_user.id}, role={user_role}, 会话客户ID={conversation.customer_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权在此会话中发送消息"
        )
    
    # 创建新消息
    new_message = Message(
        id=f"msg_{uuid4().hex}",
        conversation_id=conversation_id,
        content=message_in.content,
        type=message_in.type,
        sender_id=current_user.id,
        sender_type=user_role or "user",
        is_read=False,
        is_important=message_in.is_important
    )
    
    # 保存到数据库
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    
    # 更新会话的更新时间
    conversation.updated_at = datetime.now()
    db.commit()
    
    logger.info(f"消息创建成功: message_id={new_message.id}")
    
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
    
    # 使用辅助函数构建符合 MessageSchema 的响应
    message_response = convert_message_to_schema(new_message)
    
    return message_response

# 添加一个健康检查端点，用于测试API可用性
@router.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

# 辅助函数：将数据库消息模型转换为API响应格式
def convert_message_to_schema(message):
    """
    将数据库消息模型转换为API响应格式
    
    Args:
        message: 数据库消息模型
        
    Returns:
        dict: API响应格式的消息
    """
    if not message:
        return None
    
    # 处理发送者信息
    if message.sender_id and message.sender:
        sender = MessageSender(
            id=message.sender_id,
            name=message.sender.username if hasattr(message.sender, 'username') else "未知用户",
            avatar=message.sender.avatar if hasattr(message.sender, 'avatar') else None,
            type=message.sender_type
        )
    else:
        # 如果没有发送者信息（可能是系统消息）
        sender = MessageSender(
            id=message.sender_id or "system",
            name="系统" if message.sender_type == "system" else "AI助手" if message.sender_type == "ai" else "未知用户",
            avatar=None,
            type=message.sender_type
        )
    
    # 创建一个字典表示消息
    return {
        "id": message.id,
        "conversation_id": message.conversation_id,
        "content": message.content,
        "type": message.type,
        "sender": sender,
        "timestamp": message.timestamp,
        "is_read": message.is_read,
        "is_important": message.is_important
    }

# 辅助函数：将数据库会话模型转换为API响应格式
def convert_conversation_to_schema(conversation, db=None):
    """
    将数据库会话模型转换为API响应格式
    
    Args:
        conversation: 数据库会话模型
        db: 数据库会话对象，用于加载最后一条消息（如果未提供，则不加载）
        
    Returns:
        dict: API响应格式的会话
    """
    if not conversation:
        return None
    
    # 构建会话数据
    result = {
        "id": conversation.id,
        "title": conversation.title,
        "customer_id": conversation.customer_id,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "is_active": conversation.is_active,
        "last_message": None
    }
    
    # 获取客户信息
    customer_data = None
    
    if conversation.customer:
        # 直接使用关联的customer对象（如果已加载）
        customer = conversation.customer
        customer_data = {
            "id": customer.id,
            "username": customer.username,
            "email": customer.email,
            "avatar": customer.avatar
        }
        result["customer"] = customer_data
        logger.debug(f"已从关联对象加载会话 {conversation.id} 的客户信息: {customer.username}")
    elif db and conversation.customer_id:
        # 如果关联对象未加载但传递了数据库会话，则查询客户信息
        from app.db.models.user import User
        customer = db.query(User).filter(User.id == conversation.customer_id).first()
        if customer:
            # 将客户信息添加到结果中
            customer_data = {
                "id": customer.id,
                "username": customer.username,
                "email": customer.email,
                "avatar": customer.avatar
            }
            result["customer"] = customer_data
            # 记录日志，确认客户信息已正确加载
            logger.debug(f"已从数据库加载会话 {conversation.id} 的客户信息: {customer.username}")
        else:
            logger.warning(f"未找到会话 {conversation.id} 的客户信息，客户ID: {conversation.customer_id}")
    else:
        logger.warning(f"无法加载会话 {conversation.id} 的客户信息: customer_id={conversation.customer_id}, db={'已提供' if db else '未提供'}")
    
    # 记录最终的customer数据用于调试
    logger.info(f"会话 {conversation.id} 最终客户数据: {customer_data}")
    
    # 如果提供了数据库会话，加载最后一条消息
    if db:
        last_message = db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).order_by(Message.timestamp.desc()).first()
        
        if last_message:
            result["last_message"] = convert_message_to_schema(last_message)
    
    return result 