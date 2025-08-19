"""
聊天服务 - 整合消息和会话管理功能
"""
from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from datetime import datetime
import logging

from app.db.models.chat import Conversation, Message
from app.db.models.user import User
from app.db.uuid_utils import conversation_id
from app.schemas.chat import ConversationCreate, ConversationInfo, MessageInfo
from app.core.events import event_bus, EventTypes, create_user_event
from .message_service import MessageService
from .ai_response_service import AIResponseService
from .conversation_matcher import ConversationMatcher
from app.services.broadcasting_service import BroadcastingService

logger = logging.getLogger(__name__)


class ChatService:
    """聊天服务类 - 整合会话和消息管理"""
    
    def __init__(self, db: Session, broadcasting_service: BroadcastingService = None):
        self.db = db
        self.message_service = MessageService(db)
        self.ai_response_service = AIResponseService(db)
        self.conversation_matcher = ConversationMatcher(db)
        self.broadcasting_service = broadcasting_service
        
        # 订阅WebSocket事件
        event_bus.subscribe_async(EventTypes.WS_CONNECT, self.handle_user_connect)
        event_bus.subscribe_async(EventTypes.WS_DISCONNECT, self.handle_user_disconnect)
    
    async def handle_user_connect(self, event):
        """处理用户连接事件"""
        logger.info(f"用户连接到会话: user_id={event.user_id}, conversation_id={event.conversation_id}")
        
        # 可以在这里实现连接后的逻辑
        # 例如：更新用户在线状态、发送欢迎消息等
    
    async def handle_user_disconnect(self, event):
        """处理用户断开连接事件"""
        logger.info(f"用户断开会话连接: user_id={event.user_id}, conversation_id={event.conversation_id}")
        
        # 可以在这里实现断开后的逻辑
        # 例如：更新用户离线状态、保存会话状态等

    def _verify_conversation_access(
        self,
        conversation_id: str,
        user_id: str,
        user_role: str
    ) -> bool:
        """验证用户对会话的访问权限（内部方法）"""
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            return False
        
        # 检查访问权限
        if user_role == "customer" and conversation.customer_id != user_id:
            return False
        
        return True

    async def create_conversation(
        self,
        title: str,
        owner_id: str,
        conversation_type: str = "single",
        auto_assign_consultant: bool = True
    ) -> ConversationInfo:
        """创建新会话 - 使用新的数据库模型结构"""
        logger.info(f"创建会话: title={title}, owner_id={owner_id}, type={conversation_type}")
        
        # 创建会话 - 使用新的字段结构
        new_conversation = Conversation(
            id=conversation_id(),
            title=title,
            type=conversation_type,
            owner_id=owner_id,
            is_active=True,
            is_archived=False,
            message_count=0,
            unread_count=0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.db.add(new_conversation)
        self.db.flush()  # 获取ID
        
        # 创建会话参与者 - 所有者
        from app.db.models.chat import ConversationParticipant
        from app.db.uuid_utils import message_id
        
        owner_participant = ConversationParticipant(
            id=message_id(),
            conversation_id=new_conversation.id,
            user_id=owner_id,
            role="owner",
            takeover_status="no_takeover",  # 默认不接管
            is_active=True
        )
        self.db.add(owner_participant)
        
        # 如果需要自动分配顾问
        if auto_assign_consultant:
            # 获取用户信息
            owner = self.db.query(User).filter(User.id == owner_id).first()
            if owner:
                # 使用匹配器找到最佳顾问
                best_consultant_id = self.conversation_matcher.find_best_consultant(
                    customer_id=owner_id,
                    conversation_content=title,
                    customer_tags=[]  # 可以从用户档案获取标签
                )
                
                if best_consultant_id:
                    # 添加顾问作为参与者
                    consultant_participant = ConversationParticipant(
                        id=message_id(),
                        conversation_id=new_conversation.id,
                        user_id=best_consultant_id,
                        role="member",
                        takeover_status="no_takeover",  # 默认不接管
                        is_active=True
                    )
                    self.db.add(consultant_participant)
                    logger.info(f"自动分配顾问参与者: {best_consultant_id}")
        
        self.db.commit()
        self.db.refresh(new_conversation)
        
        # 创建欢迎消息 - 使用新的结构化格式
        welcome_text = "欢迎来到安美智享！我是您的AI助手，有什么可以帮助您的吗？"
        
        # 检查是否有数字人可以发送欢迎消息
        from app.db.models.digital_human import DigitalHuman
        user_digital_human = (
            self.db.query(DigitalHuman)
            .filter(and_(
                DigitalHuman.user_id == owner_id,
                DigitalHuman.status == "active",
                DigitalHuman.is_system_created == True
            ))
            .first()
        )
        
        if user_digital_human and user_digital_human.greeting_message:
            welcome_text = user_digital_human.greeting_message
            # 由数字人发送欢迎消息
            self.message_service.create_message(
                conversation_id=new_conversation.id,
                content={"text": welcome_text},
                message_type="text",
                sender_digital_human_id=user_digital_human.id,
                sender_type="digital_human"
            )
        else:
            # 系统发送欢迎消息
            self.message_service.create_message(
                conversation_id=new_conversation.id,
                content={"text": welcome_text},
                message_type="text",
                sender_id=None,
                sender_type="system"
            )
        
        logger.info(f"会话创建成功: id={new_conversation.id}")
        return ConversationInfo.from_model(new_conversation)
    
    def get_conversations(
        self,
        user_id: str,
        user_role: str,
        target_user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ConversationInfo]:
        """获取用户的会话列表 - 使用新的权限模型"""
        logger.info(f"获取会话列表: user_id={user_id}, role={user_role}, target_user_id={target_user_id}")
        
        from app.db.models.chat import ConversationParticipant
        
        # 基础查询
        query = self.db.query(Conversation).options(
            joinedload(Conversation.owner)
        )
        
        # 根据角色和权限过滤会话
        if target_user_id:
            # 如果指定了目标用户ID，获取该用户的会话
            if user_role in ["admin", "operator"]:
                # 管理员可以查看任何用户的会话
                query = query.filter(Conversation.owner_id == target_user_id)
            else:
                # 非管理员只能查看自己的会话
                if target_user_id != user_id:
                    raise ValueError("无权限查看其他用户的会话")
                query = query.filter(Conversation.owner_id == user_id)
        else:
            # 没有指定目标用户，根据角色决定查看范围
            if user_role == "customer":
                # 客户只能看自己拥有的会话
                query = query.filter(Conversation.owner_id == user_id)
            elif user_role in ["consultant", "doctor"]:
                # 顾问和医生可以看到自己参与的会话
                participant_conversation_ids = (
                    self.db.query(ConversationParticipant.conversation_id)
                    .filter(and_(
                        ConversationParticipant.user_id == user_id,
                        ConversationParticipant.is_active == True
                    ))
                    .all()
                )
                participant_ids = [p.conversation_id for p in participant_conversation_ids]
                
                query = query.filter(
                    or_(
                        Conversation.owner_id == user_id,
                        Conversation.id.in_(participant_ids)
                    )
                )
            elif user_role in ["admin", "operator"]:
                # 管理员可以看到所有会话
                pass
            else:
                raise ValueError(f"未知用户角色: {user_role}")
        
        conversations = query.order_by(
            Conversation.updated_at.desc()
        ).offset(skip).limit(limit).all()
        
        logger.info(f"查询到 {len(conversations)} 个会话")
        return [ConversationInfo.from_model(conv) for conv in conversations]
    
    def get_conversation_by_id(
        self,
        conversation_id: str,
        user_id: str,
        user_role: str
    ) -> Optional[ConversationInfo]:
        """获取指定会话"""
        # 验证访问权限
        if not self._verify_conversation_access(conversation_id, user_id, user_role):
            return None
        
        # 获取会话数据并转换为schema
        conversation = self.db.query(Conversation).options(
            joinedload(Conversation.customer)
        ).filter(Conversation.id == conversation_id).first()
        
        if not conversation:
            return None
        
        return ConversationInfo.from_model(conversation)
    
    async def send_message(
        self,
        conversation_id: str,
        content: Union[str, Dict[str, Any]],  # 支持字符串或结构化内容
        message_type: str,
        sender_id: str,
        sender_type: str,
        is_important: bool = False,
        auto_assign_on_first_message: bool = True,
        reply_to_message_id: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None
    ) -> MessageInfo:
        """发送消息 - 支持新的结构化内容格式"""
        # 验证会话存在和权限
        if not self._verify_conversation_access(conversation_id, sender_id, sender_type):
            raise ValueError(f"会话不存在或无权访问: {conversation_id}")
        
        # 获取会话对象用于后续逻辑
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        # 如果是客户的第一条消息且会话未分配顾问，自动分配
        if (auto_assign_on_first_message and 
            sender_type == 'customer' and 
            not conversation.assigned_consultant_id):
            
            # 检查是否是第一条用户消息
            existing_user_messages = self.db.query(Message).filter(
                Message.conversation_id == conversation_id,
                Message.sender_type == 'customer'
            ).count()
            
            if existing_user_messages == 0:  # 这是第一条用户消息
                # 获取客户信息
                customer = self.db.query(User).filter(User.id == conversation.customer_id).first()
                customer_tags = getattr(customer, 'tags', []) if customer else []
                
                # 提取文本内容用于顾问匹配
                text_for_matching = content
                if isinstance(content, dict) and 'text' in content:
                    text_for_matching = content['text']
                elif isinstance(content, dict):
                    # 如果是其他结构化内容，转换为字符串
                    text_for_matching = str(content)
                
                # 使用匹配器找到最佳顾问
                best_consultant_id = self.conversation_matcher.find_best_consultant(
                    customer_id=conversation.customer_id,
                    conversation_content=text_for_matching,
                    customer_tags=customer_tags
                )
                
                if best_consultant_id:
                    # 分配顾问
                    success = await self.conversation_matcher.assign_conversation_to_consultant(
                        conversation_id, best_consultant_id
                    )
                    if success:
                        logger.info(f"首条消息触发顾问分配: {conversation_id} -> {best_consultant_id}")
        
        # 创建消息
        message = await self.message_service.create_message(
            conversation_id=conversation_id,
            content=content,
            message_type=message_type,
            sender_id=sender_id,
            sender_type=sender_type,
            is_important=is_important,
            reply_to_message_id=reply_to_message_id,
            extra_metadata=extra_metadata
        )
        
        # 通过新的广播服务发送消息通知
        if self.broadcasting_service:
            try:
                await self.broadcasting_service.broadcast_message(
                    conversation_id=conversation_id,
                    message_data=message.dict(),  # 转换为字典格式
                    exclude_user_id=sender_id  # 排除发送者
                )
                logger.info(f"消息广播成功: message_id={message.id}")
            except Exception as e:
                logger.error(f"消息广播失败: message_id={message.id}, error={e}")
        else:
            logger.warning("BroadcastingService未注入，消息未广播")
        
        return message

    async def send_text_message(
        self,
        conversation_id: str,
        text: str,
        sender_id: str,
        sender_type: str,
        is_important: bool = False,
        reply_to_message_id: Optional[str] = None
    ) -> MessageInfo:
        """便利方法：发送文本消息"""
        message = self.message_service.create_text_message(
            conversation_id=conversation_id,
            text=text,
            sender_id=sender_id,
            sender_type=sender_type,
            is_important=is_important,
            reply_to_message_id=reply_to_message_id
        )
        
        # 广播消息
        if self.broadcasting_service:
            try:
                await self.broadcasting_service.broadcast_message(
                    conversation_id=conversation_id,
                    message_data=message.dict(),
                    exclude_user_id=sender_id
                )
            except Exception as e:
                logger.error(f"文本消息广播失败: {e}")
        
        return message

    async def send_media_message(
        self,
        conversation_id: str,
        media_url: str,
        media_name: str,
        mime_type: str,
        size_bytes: int,
        sender_id: str,
        sender_type: str,
        text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        is_important: bool = False,
        reply_to_message_id: Optional[str] = None,
        upload_method: Optional[str] = None
    ) -> MessageInfo:
        """便利方法：发送媒体消息"""
        message = await self.message_service.create_media_message(
            conversation_id=conversation_id,
            media_url=media_url,
            media_name=media_name,
            mime_type=mime_type,
            size_bytes=size_bytes,
            sender_id=sender_id,
            sender_type=sender_type,
            text=text,
            metadata=metadata,
            is_important=is_important,
            reply_to_message_id=reply_to_message_id,
            upload_method=upload_method
        )
        
        # 广播消息
        if self.broadcasting_service:
            try:
                await self.broadcasting_service.broadcast_message(
                    conversation_id=conversation_id,
                    message_data=message.dict(),
                    exclude_user_id=sender_id
                )
            except Exception as e:
                logger.error(f"媒体消息广播失败: {e}")
        
        return message

    async def send_system_event_message(
        self,
        conversation_id: str,
        event_type: str,
        status: str,
        sender_id: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None
    ) -> MessageInfo:
        """便利方法：发送系统事件消息"""
        message = await self.message_service.create_system_event_message(
            conversation_id=conversation_id,
            event_type=event_type,
            status=status,
            sender_id=sender_id,
            event_data=event_data
        )
        
        # 广播消息
        if self.broadcasting_service:
            try:
                await self.broadcasting_service.broadcast_message(
                    conversation_id=conversation_id,
                    message_data=message.dict(),
                    exclude_user_id=None  # 系统消息广播给所有人
                )
            except Exception as e:
                logger.error(f"系统事件消息广播失败: {e}")
        
        return message

    async def send_message_and_broadcast(
        self,
        conversation_id: str,
        content: Union[str, Dict[str, Any]],
        message_type: str,
        sender_id: str,
        sender_type: str,
        is_important: bool = False,
        auto_assign_on_first_message: bool = True
    ) -> MessageInfo:
        """
        发送消息并广播（保持API兼容性）
        
        这个方法整合了消息保存和实时广播功能，是send_message的别名
        """
        return await self.send_message(
            conversation_id=conversation_id,
            content=content,
            message_type=message_type,
            sender_id=sender_id,
            sender_type=sender_type,
            is_important=is_important,
            auto_assign_on_first_message=auto_assign_on_first_message
        )
    
    def get_conversation_messages(
        self,
        conversation_id: str,
        user_id: str,
        user_role: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[MessageInfo]:
        """获取会话消息"""
        # 验证访问权限
        conversation = self.get_conversation_by_id(conversation_id, user_id, user_role)
        if not conversation:
            raise ValueError(f"会话不存在或无权访问: {conversation_id}")
        
        # 使用MessageService获取消息并返回正确的schema类型
        return self.message_service.get_conversation_messages(
            conversation_id, skip, limit
        )
    
    def mark_messages_as_read(
        self,
        message_ids: List[str],
        user_id: str
    ) -> int:
        """标记消息为已读"""
        return self.message_service.mark_messages_as_read(message_ids, user_id)
    
    def get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """获取会话摘要信息,不仅是sumary字段，还有消息统计和最后一条消息"""
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            return None
        
        # 获取消息统计
        total_messages = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).count()
        
        # 获取最后一条消息
        last_message = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.timestamp.desc()).first()
        
        return {
            "id": conversation.id,
            "title": conversation.title,
            "customer_id": conversation.customer_id,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
            "is_active": conversation.is_active,
            "total_messages": total_messages,
            "last_message": MessageInfo.from_model(last_message) if last_message else None
        }
    
    
    def search_conversations(
        self,
        user_id: str,
        user_role: str,
        query: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[ConversationInfo]:
        """搜索会话"""
        base_query = self.db.query(Conversation).options(
            joinedload(Conversation.customer)
        )
        # 根据角色过滤
        if user_role == "customer":
            base_query = base_query.filter(Conversation.customer_id == user_id)
        # 搜索条件
        if query:
            base_query = base_query.filter(
                Conversation.title.ilike(f"%{query}%")
            )
        conversations = base_query.order_by(
            Conversation.updated_at.desc()
        ).offset(skip).limit(limit).all()
        # 转换为 ConversationInfo
        result = []
        for conv in conversations:
            last_message = self.db.query(Message).filter(
                Message.conversation_id == conv.id
            ).order_by(Message.timestamp.desc()).first()
            result.append(ConversationInfo.from_model(conv, last_message))
        return result
    
    async def close_conversation(self, conversation_id: str, user_id: str):
        """关闭会话"""
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise ValueError(f"会话不存在: {conversation_id}")
        
        conversation.is_active = False
        conversation.updated_at = datetime.now()
        
        # 创建关闭消息
        self.message_service.create_system_event_message(
            conversation_id=conversation_id,
            event_type="conversation_closed",
            status="closed",
            event_data={"closed_by": user_id}
        )
        
        self.db.commit()
        logger.info(f"会话已关闭: {conversation_id}")
    
    async def reopen_conversation(self, conversation_id: str, user_id: str):
        """重新打开会话"""
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise ValueError(f"会话不存在: {conversation_id}")
        
        conversation.is_active = True
        conversation.updated_at = datetime.now()
        
        # 创建重新打开消息
        await self.message_service.create_message(
            conversation_id=conversation_id,
            content="会话已重新打开",
            message_type="system",
            sender_id=user_id,
            sender_type="system"
        )
        
        self.db.commit()
        logger.info(f"会话已重新打开: {conversation_id}")
    
    def get_ai_controlled_status(self, conversation_id: str) -> Optional[bool]:
        """查询会话当前是否为AI控制"""
        conversation = self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation:
            return conversation.is_ai_controlled
        return None

    def set_ai_controlled_status(self, conversation_id: str, is_ai_controlled: bool) -> bool:
        """设置会话AI控制状态"""
        conversation = self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            return False
        conversation.is_ai_controlled = is_ai_controlled
        conversation.updated_at = datetime.now()
        self.db.commit()
        return True
    
    def update_conversation(
        self,
        conversation_id: str,
        user_id: str,
        user_role: str,
        update_data: Dict[str, Any]
    ) -> Optional[ConversationInfo]:
        """更新会话信息"""
        # 验证访问权限
        if not self._verify_conversation_access(conversation_id, user_id, user_role):
            raise PermissionError(f"无权修改会话: {conversation_id}")
        
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            return None
        
        # 更新允许的字段
        allowed_fields = ["title", "status"]
        for field, value in update_data.items():
            if field in allowed_fields and hasattr(conversation, field):
                setattr(conversation, field, value)
        
        conversation.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(conversation)
        
        logger.info(f"会话已更新: conversation_id={conversation_id}, fields={list(update_data.keys())}")
        return ConversationInfo.from_model(conversation)

    def mark_message_as_important(
        self,
        conversation_id: str,
        message_id: str,
        is_important: bool,
        user_id: str,
        user_role: str
    ) -> bool:
        """标记消息为重点"""
        # 验证会话访问权限
        if not self._verify_conversation_access(conversation_id, user_id, user_role):
            raise PermissionError(f"无权访问会话: {conversation_id}")
        
        # 调用消息服务标记重点
        success = self.message_service.mark_message_as_important(message_id, is_important)
        
        if not success:
            raise ValueError(f"消息不存在: {message_id}")
        
        logger.info(f"消息重点状态已更新: conversation_id={conversation_id}, message_id={message_id}, is_important={is_important}")
        return True 