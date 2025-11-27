"""
聊天服务 - 核心业务逻辑
处理会话和消息管理等功能
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc
from datetime import datetime

from app.chat.models.chat import Conversation, Message, ConversationParticipant
from app.chat.schemas.chat import (
    ConversationInfo, MessageInfo, ConversationCreate,
    CreateTextMessageRequest, CreateMediaMessageRequest,
    CreateSystemEventRequest, CreateStructuredMessageRequest,
    MessageCreateRequest
)
# 移除转换器导入，直接使用 schema 的 from_model 方法
from app.identity_access.models.user import User
from app.common.deps.uuid_utils import conversation_id, message_id
from app.core.api import BusinessException, ErrorCode
from app.websocket.broadcasting_service import BroadcastingService

logger = logging.getLogger(__name__)


class ChatService:
    """聊天服务 - 直接操作数据库模型"""
    
    def __init__(self, db: Session, broadcasting_service: Optional[BroadcastingService] = None):
        self.db = db
        self.broadcasting_service = broadcasting_service
    
    # ============ 会话管理 ============
    
    def create_conversation(
        self,
        title: str,
        owner_id: str,
        chat_mode: str = "single",
        tag: str = "chat"
    ) -> ConversationInfo:
        """创建会话"""
        # 验证标题
        if not title or not title.strip():
            raise BusinessException("会话标题不能为空", code=ErrorCode.INVALID_INPUT)
        
        # 创建会话
        conversation = Conversation(
            id=conversation_id(),
            title=title,
            owner_id=owner_id,
            chat_mode=chat_mode,
            tag=tag,
            is_active=True,
            message_count=0,
            unread_count=0
        )
        
        self.db.add(conversation)
        self.db.flush()  # 获取ID
        
        # 创建参与者
        participant = ConversationParticipant(
            id=conversation_id(),  # 复用ID生成器
            conversation_id=conversation.id,
            user_id=owner_id,
            role="owner",
            is_active=True
        )
        self.db.add(participant)
        
        # 创建欢迎消息
        welcome_message = Message(
            id=message_id(),
            conversation_id=conversation.id,
            content={
                "type": "system",
                "system_event_type": "welcome",
                "message": "欢迎来到安美智享！我是您的AI助手，有什么可以帮助您的吗？"
            },
            type="system",
            sender_type="system",
            is_read=True
        )
        self.db.add(welcome_message)
        
        conversation.message_count = 1
        conversation.last_message_at = datetime.now()
        conversation.first_participant_id = owner_id
        
        self.db.commit()
        self.db.refresh(conversation)
        
        # 加载关联数据
        # 注意：joinedload 不支持 limit，需要在查询后手动处理最后一条消息
        conversation = self.db.query(Conversation).options(
            joinedload(Conversation.owner),
            joinedload(Conversation.participants).joinedload(ConversationParticipant.user)
        ).filter(Conversation.id == conversation.id).first()
        
        # 手动加载最后一条消息
        if conversation:
            last_message = self.db.query(Message).filter(
                Message.conversation_id == conversation.id
            ).order_by(desc(Message.timestamp)).limit(1).first()
            if last_message:
                conversation.messages = [last_message]
            else:
                conversation.messages = []
        
        # 转换为响应Schema
        from app.chat.schemas.chat import ConversationInfo, MessageInfo
        
        last_message = None
        if conversation.messages:
            last_msg = conversation.messages[0]
            if last_msg:
                last_message = MessageInfo.from_model(last_msg)
        
        return ConversationInfo.from_model(conversation, last_message=last_message)
    
    def get_user_role(self, user: User) -> str:
        """获取用户的当前角色，并映射到sender_type枚举值"""
        from app.identity_access.deps.permission_deps import get_user_primary_role
        logger.info(f"服务：获取用户角色 - user_id={user.id}")
        role = get_user_primary_role(user)
        logger.info(f"服务：获取到用户角色 = {role}")
        
        # 将角色映射到sender_type枚举值
        # sender_type枚举值：customer, consultant, doctor, system, digital_human
        role_mapping = {
            "admin": "consultant",  # 管理员映射为顾问
            "administrator": "consultant",
            "super_admin": "consultant",
            "customer": "customer",
            "consultant": "consultant",
            "doctor": "doctor",
            "operator": "consultant",  # 操作员映射为顾问
            "system": "system",
            "digital_human": "digital_human"
        }
        
        mapped_role = role_mapping.get(role, "customer")  # 默认映射为customer
        logger.info(f"服务：角色映射 {role} -> {mapped_role}")
        return mapped_role
    
    def get_conversations(
        self,
        user_id: str,
        user_role: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ConversationInfo]:
        """获取用户会话列表（支持角色过滤）"""
        # 查询用户作为参与者的会话ID列表
        participant_conv_ids_query = self.db.query(ConversationParticipant.conversation_id).filter(
            ConversationParticipant.user_id == user_id,
            ConversationParticipant.is_active == True
        )
        participant_conv_ids = [row[0] for row in participant_conv_ids_query.all()]
        
        # 查询用户作为owner或参与者的会话
        query = self.db.query(Conversation).options(
            joinedload(Conversation.owner)
        )
        
        if participant_conv_ids:
            query = query.filter(
                or_(
                    Conversation.owner_id == user_id,
                    Conversation.id.in_(participant_conv_ids)
                )
            )
        else:
            query = query.filter(Conversation.owner_id == user_id)
        
        # 根据角色过滤（如果需要）
        # 目前简化处理，后续可以根据角色扩展权限逻辑
        
        conversations = query.order_by(
            desc(Conversation.last_message_at),
            desc(Conversation.created_at)
        ).offset(skip).limit(limit).all()
        
        # 转换为响应Schema，并手动加载最后一条消息
        from app.chat.schemas.chat import ConversationInfo, MessageInfo
        result = []
        for conv in conversations:
            # 手动查询最后一条消息
            last_msg = self.db.query(Message).filter(
                Message.conversation_id == conv.id
            ).order_by(desc(Message.timestamp)).limit(1).first()
            
            last_message = None
            if last_msg:
                last_message = MessageInfo.from_model(last_msg)
            
            result.append(ConversationInfo.from_model(conv, last_message=last_message))
        return result
    
    def get_user_conversations(
        self,
        user_id: str,
        chat_mode: Optional[str] = None,
        tag: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ConversationInfo]:
        """获取用户会话列表（旧方法，保持兼容）"""
        # 查询用户作为参与者的会话ID列表
        participant_conv_ids_query = self.db.query(ConversationParticipant.conversation_id).filter(
            ConversationParticipant.user_id == user_id,
            ConversationParticipant.is_active == True
        )
        participant_conv_ids = [row[0] for row in participant_conv_ids_query.all()]
        
        # 查询用户作为owner或参与者的会话
        query = self.db.query(Conversation).options(
            joinedload(Conversation.owner)
        )
        
        if participant_conv_ids:
            query = query.filter(
                or_(
                    Conversation.owner_id == user_id,
                    Conversation.id.in_(participant_conv_ids)
                )
            )
        else:
            query = query.filter(Conversation.owner_id == user_id)
        
        # 应用筛选
        if chat_mode:
            query = query.filter(Conversation.chat_mode == chat_mode)
        if tag:
            query = query.filter(Conversation.tag == tag)
        if is_active is not None:
            query = query.filter(Conversation.is_active == is_active)
        
        conversations = query.order_by(
            desc(Conversation.last_message_at),
            desc(Conversation.created_at)
        ).offset(offset).limit(limit).all()
        
        # 转换为响应Schema，并手动加载最后一条消息
        from app.chat.schemas.chat import ConversationInfo, MessageInfo
        result = []
        for conv in conversations:
            # 手动查询最后一条消息
            last_msg = self.db.query(Message).filter(
                Message.conversation_id == conv.id
            ).order_by(desc(Message.timestamp)).limit(1).first()
            
            last_message = None
            if last_msg:
                last_message = MessageInfo.from_model(last_msg)
            
            result.append(ConversationInfo.from_model(conv, last_message=last_message))
        return result
    
    def get_conversation(
        self,
        conversation_id: str,
        user_id: Optional[str] = None
    ) -> Optional[ConversationInfo]:
        """获取会话详情"""
        # 注意：joinedload 不支持 order_by，需要在查询后手动处理消息
        query = self.db.query(Conversation).options(
            joinedload(Conversation.owner),
            joinedload(Conversation.participants).joinedload(ConversationParticipant.user)
        ).filter(Conversation.id == conversation_id)
        
        # 权限检查：检查用户是否是owner或参与者
        if user_id:
            # 先查询会话是否存在
            conversation = query.first()
            if not conversation:
                return None
            
            # 检查用户是否是owner
            if str(conversation.owner_id) == user_id:
                pass  # 是owner，允许访问
            else:
                # 检查用户是否是参与者
                participant = self.db.query(ConversationParticipant).filter(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.user_id == user_id,
                    ConversationParticipant.is_active == True
                ).first()
                
                if not participant:
                    # 既不是owner也不是参与者，拒绝访问
                    return None
        else:
            conversation = query.first()
            if not conversation:
                return None
        
        # 转换为响应Schema
        from app.chat.schemas.chat import ConversationInfo, MessageInfo
        # 手动查询最后一条消息（按时间戳排序）
        last_msg = self.db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).order_by(desc(Message.timestamp)).limit(1).first()
        
        last_message = None
        if last_msg:
            last_message = MessageInfo.from_model(last_msg)
        
        return ConversationInfo.from_model(conversation, last_message=last_message)
    
    def get_conversation_by_id_use_case(
        self,
        conversation_id: str,
        user_id: str,
        user_role: Optional[str] = None
    ) -> Optional[ConversationInfo]:
        """根据ID获取会话（用例方法）"""
        return self.get_conversation(conversation_id=conversation_id, user_id=user_id)
    
    def update_conversation(
        self,
        conversation_id: str,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Optional[ConversationInfo]:
        """更新会话信息"""
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.owner_id == user_id
        ).first()
        
        if not conversation:
            return None
        
        # 更新字段
        allowed_fields = ['title', 'is_active', 'is_archived', 'is_pinned', 'tag']
        for field, value in updates.items():
            if field in allowed_fields and hasattr(conversation, field):
                setattr(conversation, field, value)
        
        if 'is_pinned' in updates and updates['is_pinned']:
            conversation.pinned_at = datetime.now()
        elif 'is_pinned' in updates and not updates['is_pinned']:
            conversation.pinned_at = None
        
        self.db.commit()
        self.db.refresh(conversation)
        
        # 加载关联数据并转换
        conversation = self.db.query(Conversation).options(
            joinedload(Conversation.owner),
            joinedload(Conversation.participants).joinedload(ConversationParticipant.user)
        ).filter(Conversation.id == conversation.id).first()
        
        from app.chat.schemas.chat import ConversationInfo, MessageInfo
        last_message = None
        if conversation:
            # 手动查询最后一条消息
            last_msg = self.db.query(Message).filter(
                Message.conversation_id == conversation.id
            ).order_by(desc(Message.timestamp)).limit(1).first()
            
            if last_msg:
                last_message = MessageInfo.from_model(last_msg)
        
        return ConversationInfo.from_model(conversation, last_message=last_message)
    
    # ============ 消息管理 ============
    
    def create_text_message(
        self,
        conversation_id: str,
        sender_id: str,
        content: str,
        sender_type: str = "customer",
        reply_to_message_id: Optional[str] = None
    ) -> MessageInfo:
        """创建文本消息"""
        # 验证会话存在
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise BusinessException("会话不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
        
        # 创建消息
        message = Message(
            id=message_id(),
            conversation_id=conversation_id,
            content={
                "type": "text",
                "text": content
            },
            type="text",
            sender_id=sender_id,
            sender_type=sender_type,
            is_read=False,
            reply_to_message_id=reply_to_message_id
        )
        
        self.db.add(message)
        
        # 更新会话统计
        conversation.message_count = (conversation.message_count or 0) + 1
        conversation.last_message_at = datetime.now()
        if sender_type != "customer":
            conversation.unread_count = (conversation.unread_count or 0) + 1
        
        self.db.commit()
        self.db.refresh(message)
        
        # 加载关联数据
        message = self.db.query(Message).options(
            joinedload(Message.sender)
        ).filter(Message.id == message.id).first()
        
        # 转换为响应Schema
        from app.chat.schemas.chat import MessageInfo
        return MessageInfo.from_model(message)
    
    def create_media_message(
        self,
        conversation_id: str,
        sender_id: str,
        media_type: str,
        media_url: str,
        text: Optional[str] = None,
        sender_type: str = "customer"
    ) -> MessageInfo:
        """创建媒体消息"""
        # 验证会话存在
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise BusinessException("会话不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
        
        # 创建消息
        message = Message(
            id=message_id(),
            conversation_id=conversation_id,
            content={
                "type": "media",
                "media_type": media_type,
                "media_url": media_url,
                "text": text
            },
            type="media",
            sender_id=sender_id,
            sender_type=sender_type,
            is_read=False
        )
        
        self.db.add(message)
        
        # 更新会话统计
        conversation.message_count = (conversation.message_count or 0) + 1
        conversation.last_message_at = datetime.now()
        if sender_type != "customer":
            conversation.unread_count = (conversation.unread_count or 0) + 1
        
        self.db.commit()
        self.db.refresh(message)
        
        # 加载关联数据
        message = self.db.query(Message).options(
            joinedload(Message.sender)
        ).filter(Message.id == message.id).first()
        
        # 转换为响应Schema
        from app.chat.schemas.chat import MessageInfo
        return MessageInfo.from_model(message)
    
    def get_conversation_messages(
        self,
        conversation_id: str,
        limit: int = 50,
        offset: int = 0,
        before_message_id: Optional[str] = None
    ) -> List[MessageInfo]:
        """获取会话消息列表"""
        query = self.db.query(Message).options(
            joinedload(Message.sender),
            joinedload(Message.reply_to_message)
        ).filter(Message.conversation_id == conversation_id)
        
        # 分页
        if before_message_id:
            before_message = self.db.query(Message).filter(
                Message.id == before_message_id
            ).first()
            if before_message:
                query = query.filter(Message.timestamp < before_message.timestamp)
        
        messages = query.order_by(desc(Message.timestamp)).offset(offset).limit(limit).all()
        
        # 反转顺序，按时间正序返回
        messages.reverse()
        
        # 转换为响应Schema
        from app.chat.schemas.chat import MessageInfo
        return [MessageInfo.from_model(msg) for msg in messages]
    
    def mark_messages_as_read(
        self,
        conversation_id: str,
        user_id: str,
        message_ids: Optional[List[str]] = None
    ) -> int:
        """标记消息为已读"""
        query = self.db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.is_read == False,
            Message.sender_id != user_id  # 不标记自己发送的消息
        )
        
        if message_ids:
            query = query.filter(Message.id.in_(message_ids))
        
        messages = query.all()
        count = len(messages)
        
        for message in messages:
            message.is_read = True
        
        # 更新会话未读计数
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if conversation:
            conversation.unread_count = max(0, (conversation.unread_count or 0) - count)
        
        self.db.commit()
        
        return count
    
    def mark_message_as_read_use_case(self, message_id: str) -> bool:
        """标记消息为已读（用例方法）"""
        message = self.db.query(Message).filter(Message.id == message_id).first()
        if not message:
            return False
        
        message.is_read = True
        
        # 更新会话未读计数
        conversation = self.db.query(Conversation).filter(
            Conversation.id == message.conversation_id
        ).first()
        
        if conversation:
            conversation.unread_count = max(0, (conversation.unread_count or 0) - 1)
        
        self.db.commit()
        return True
    
    def mark_message_as_important_use_case(
        self,
        message_id: str,
        is_important: bool
    ) -> bool:
        """标记消息为重点（用例方法）"""
        message = self.db.query(Message).filter(Message.id == message_id).first()
        if not message:
            return False
        
        message.is_important = is_important
        self.db.commit()
        return True
    
    async def broadcast_message_safe(
        self,
        conversation_id: str,
        message_info: MessageInfo,
        sender_id: str
    ):
        """安全地广播消息"""
        if not self.broadcasting_service:
            logger.warning("广播服务未配置，跳过消息广播")
            return
        
        try:
            message_data = message_info.model_dump() if hasattr(message_info, 'model_dump') else message_info.dict()
            await self.broadcasting_service.broadcast_message(
                conversation_id=conversation_id,
                message_data=message_data,
                exclude_user_id=sender_id
            )
        except Exception as e:
            logger.error(f"广播消息失败: {e}", exc_info=True)
    
    # ============ 消息创建用例方法 ============
    
    def create_message_use_case(
        self,
        conversation_id: str,
        request: MessageCreateRequest,
        sender: User
    ) -> MessageInfo:
        """创建通用消息用例"""
        sender_role = self.get_user_role(sender)
        
        # 验证content字段
        if not request.content:
            raise BusinessException("消息内容不能为空", code=ErrorCode.INVALID_INPUT)
        
        # 根据消息类型分发到对应的创建方法
        if request.type == "text":
            # 从 content 中提取文本
            if not isinstance(request.content, dict):
                logger.error(f"文本消息content格式错误: content={request.content}, type={type(request.content)}")
                raise ValueError(f"文本消息内容格式不正确，期望字典格式，实际: {type(request.content)}")
            
            text = request.content.get("text", "")
            if not text:
                logger.error(f"文本消息内容为空: content={request.content}")
                raise BusinessException("消息文本内容不能为空", code=ErrorCode.INVALID_INPUT)
            
            logger.info(f"创建文本消息: conversation_id={conversation_id}, text_length={len(text)}")
            return self.create_text_message(
                conversation_id=conversation_id,
                sender_id=str(sender.id),
                content=text,
                sender_type=sender_role,
                reply_to_message_id=request.reply_to_message_id
            )
        elif request.type == "media":
            # 从 content 中提取媒体信息
            if isinstance(request.content, dict):
                media_url = request.content.get("media_url", "")
                media_type = request.content.get("media_type", "image")
                text = request.content.get("text")
                return self.create_media_message(
                    conversation_id=conversation_id,
                    sender_id=str(sender.id),
                    media_type=media_type,
                    media_url=media_url,
                    text=text,
                    sender_type=sender_role
                )
            else:
                raise ValueError("媒体消息内容格式不正确")
        else:
            raise ValueError(f"不支持的消息类型: {request.type}")
    
    def create_text_message_use_case(
        self,
        conversation_id: str,
        request: CreateTextMessageRequest,
        sender: User
    ) -> MessageInfo:
        """创建文本消息用例"""
        sender_role = self.get_user_role(sender)
        return self.create_text_message(
            conversation_id=conversation_id,
            sender_id=str(sender.id),
            content=request.text,
            sender_type=sender_role,
            reply_to_message_id=request.reply_to_message_id
        )
    
    def create_media_message_use_case(
        self,
        conversation_id: str,
        request: CreateMediaMessageRequest,
        sender: User
    ) -> MessageInfo:
        """创建媒体消息用例"""
        sender_role = self.get_user_role(sender)
        # 从请求中提取媒体类型（可以根据 media_url 或 mime_type 推断）
        media_type = getattr(request, 'media_type', 'image')
        if hasattr(request, 'mime_type') and request.mime_type:
            # 根据 mime_type 推断媒体类型
            if request.mime_type.startswith('image'):
                media_type = 'image'
            elif request.mime_type.startswith('video'):
                media_type = 'video'
            elif request.mime_type.startswith('audio'):
                media_type = 'audio'
        
        return self.create_media_message(
            conversation_id=conversation_id,
            sender_id=str(sender.id),
            media_type=media_type,
            media_url=request.media_url,
            text=getattr(request, 'text', None),
            sender_type=sender_role
        )
    
    def create_system_event_message_use_case(
        self,
        conversation_id: str,
        request: CreateSystemEventRequest,
        sender: User
    ) -> MessageInfo:
        """创建系统事件消息用例"""
        # 权限检查：只有管理员可以创建系统事件消息
        sender_role = self.get_user_role(sender)
        if sender_role not in ["admin", "system"]:
            raise PermissionError("只有管理员可以创建系统事件消息")
        
        # 验证会话存在
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise BusinessException("会话不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
        
        # 创建系统消息
        event_data = request.event_data or {}
        message = Message(
            id=message_id(),
            conversation_id=conversation_id,
            content={
                "type": "system",
                "system_event_type": request.event_type,
                **event_data
            },
            type="system",
            sender_type="system",
            is_read=True
        )
        
        self.db.add(message)
        
        # 更新会话统计
        conversation.message_count = (conversation.message_count or 0) + 1
        conversation.last_message_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(message)
        
        # 转换为响应Schema
        from app.chat.schemas.chat import MessageInfo
        return MessageInfo.from_model(message)
    
    def create_structured_message_use_case(
        self,
        conversation_id: str,
        request: CreateStructuredMessageRequest,
        sender: User
    ) -> MessageInfo:
        """创建结构化消息用例"""
        sender_role = self.get_user_role(sender)
        
        # 验证会话存在
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise BusinessException("会话不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
        
        # 创建结构化消息
        message = Message(
            id=message_id(),
            conversation_id=conversation_id,
            content={
                "type": "structured",
                "card_type": request.card_type,
                "title": request.title,
                "data": request.data,
                **getattr(request, 'actions', {})
            },
            type="structured",
            sender_id=str(sender.id),
            sender_type=sender_role,
            is_read=False,
            extra_metadata=getattr(request, 'metadata', None)
        )
        
        self.db.add(message)
        
        # 更新会话统计
        conversation.message_count = (conversation.message_count or 0) + 1
        conversation.last_message_at = datetime.now()
        if sender_role != "customer":
            conversation.unread_count = (conversation.unread_count or 0) + 1
        
        self.db.commit()
        self.db.refresh(message)
        
        # 加载关联数据
        message = self.db.query(Message).options(
            joinedload(Message.sender)
        ).filter(Message.id == message.id).first()
        
        # 转换为响应Schema
        from app.chat.schemas.chat import MessageInfo
        return MessageInfo.from_model(message)
    
    async def can_access_conversation(self, conversation_id: str, user_id: str) -> bool:
        """检查用户是否可以访问会话"""
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            return False
        
        # 检查是否是会话所有者
        if str(conversation.owner_id) == user_id:
            return True
        
        # 检查是否是参与者
        participant = self.db.query(ConversationParticipant).filter(
            and_(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.user_id == user_id
            )
        ).first()
        
        if participant:
            return True
        
        # 检查是否是管理员（通过角色判断，这里简化处理）
        from app.identity_access.models.user import User
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            role_names = [role.name for role in user.roles]
            if 'admin' in role_names or 'operator' in role_names:
                return True
        
        return False
    
    def create_media_message_with_details(
        self,
        conversation_id: str,
        sender_id: str,
        sender_type: str,
        media_url: str,
        media_name: Optional[str] = None,
        mime_type: Optional[str] = None,
        size_bytes: Optional[int] = None,
        text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        is_important: bool = False,
        upload_method: Optional[str] = None
    ) -> MessageInfo:
        """创建媒体消息（支持更多参数）"""
        # 根据 mime_type 推断 media_type
        media_type = "file"  # 默认
        if mime_type:
            if mime_type.startswith('image'):
                media_type = 'image'
            elif mime_type.startswith('video'):
                media_type = 'video'
            elif mime_type.startswith('audio'):
                media_type = 'audio'
        
        # 构建消息内容
        content = {
            "type": "media",
            "media_type": media_type,
            "media_url": media_url
        }
        
        if media_name:
            content["media_name"] = media_name
        if mime_type:
            content["mime_type"] = mime_type
        if size_bytes is not None:
            content["size_bytes"] = size_bytes
        if text:
            content["text"] = text
        if metadata:
            content.update(metadata)
        
        # 创建消息
        message = Message(
            id=message_id(),
            conversation_id=conversation_id,
            content=content,
            type="media",
            sender_id=sender_id,
            sender_type=sender_type,
            is_read=False,
            is_important=is_important
        )
        
        self.db.add(message)
        
        # 更新会话统计
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        if conversation:
            conversation.message_count = (conversation.message_count or 0) + 1
            conversation.last_message_at = datetime.now()
            if sender_type != "customer":
                conversation.unread_count = (conversation.unread_count or 0) + 1
        
        self.db.commit()
        self.db.refresh(message)
        
        # 加载关联数据
        message = self.db.query(Message).options(
            joinedload(Message.sender)
        ).filter(Message.id == message.id).first()
        
        # 转换为响应Schema
        from app.chat.schemas.chat import MessageInfo
        return MessageInfo.from_model(message)

