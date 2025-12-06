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
from app.core.api import BusinessException, ErrorCode, PaginatedRecords
from app.websocket.broadcasting_service import BroadcastingService

logger = logging.getLogger(__name__)


class ChatService:
    """聊天服务 - 直接操作数据库模型"""
    
    def __init__(self, db: Session, broadcasting_service: Optional[BroadcastingService] = None):
        self.db = db
        self.broadcasting_service = broadcasting_service
    
    # ============ 辅助方法 ============
    
    def _get_or_create_participant(
        self,
        conversation_id: str,
        user_id: str,
        default_role: str = "member"
    ) -> ConversationParticipant:
        """获取或创建参与者的个人化记录"""
        participant = self.db.query(ConversationParticipant).filter(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == user_id,
            ConversationParticipant.is_active == True
        ).first()
        
        if not participant:
            # 创建新的参与者记录
            participant = ConversationParticipant(
                id=message_id(),  # 参与者ID使用message_id生成器
                conversation_id=conversation_id,
                user_id=user_id,
                role=default_role,
                is_active=True,
                message_count=0,
                unread_count=0
            )
            self.db.add(participant)
            self.db.flush()
        
        return participant
    
    def _update_participant_stats_on_new_message(
        self,
        conversation_id: str,
        sender_id: str,
        is_system_message: bool = False
    ):
        """当有新消息时，更新所有参与者的统计信息
        
        Args:
            conversation_id: 会话ID
            sender_id: 发送者ID
            is_system_message: 是否为系统消息（系统消息不增加未读计数）
        """
        # 获取会话的所有活跃参与者
        participants = self.db.query(ConversationParticipant).filter(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.is_active == True
        ).all()
        
        now = datetime.now()
        
        for participant in participants:
            # 更新发送者消息总数
            if str(participant.user_id) == str(sender_id):
                participant.message_count = (participant.message_count or 0) + 1
                participant.last_message_at = now
            
            # 如果是发送者或是系统消息，不增加未读数；否则增加未读数
            if not is_system_message and str(participant.user_id) != str(sender_id):
                participant.unread_count = (participant.unread_count or 0) + 1
    
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
            is_active=True
        )
        
        self.db.add(conversation)
        self.db.flush()  # 获取ID
        
        # 创建参与者
        participant = ConversationParticipant(
            id=conversation_id(),  # 复用ID生成器
            conversation_id=conversation.id,
            user_id=owner_id,
            role="owner",
            is_active=True,
            message_count=0,
            unread_count=0
        )
        self.db.add(participant)
        
        self.db.commit()
        self.db.refresh(conversation)
        self.db.refresh(participant)
        
        # 加载关联数据
        # 注意：joinedload 不支持 limit，需要在查询后手动处理最后一条消息
        conversation = self.db.query(Conversation).options(
            joinedload(Conversation.owner),
            joinedload(Conversation.participants).joinedload(ConversationParticipant.user)
        ).filter(Conversation.id == conversation.id).first()
                
        return ConversationInfo.from_model(conversation, last_message=None, participant=participant)
    
    
    def get_conversations(
        self,
        user_id: str,
        user_role: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None
    ) -> PaginatedRecords[ConversationInfo]:
        """根据查询条件获取用户参与的会话列表
        
        从会话参与者表中分页查询指定用户参与的会话，支持标题模糊搜索，按修改时间倒序排列
        owner 也是参与者（角色为 owner），所以直接从 participant 表查询即可
        """
        # 从参与者表开始，JOIN 会话表
        # 这样可以查询用户作为参与者的所有会话（包括 owner 角色的会话）
        # 使用别名以便在排序中使用 participant 字段
        query = self.db.query(Conversation, ConversationParticipant).join(
            ConversationParticipant,
            Conversation.id == ConversationParticipant.conversation_id
        ).filter(
            ConversationParticipant.user_id == user_id,
            ConversationParticipant.is_active == True
        )
        
        # 如果提供了搜索关键词，对标题进行模糊匹配
        if search and search.strip():
            search_pattern = f"%{search.strip()}%"
            query = query.filter(Conversation.title.like(search_pattern))
        
        # 获取总数（在分页之前）
        total = query.count()
        
        # 按个人化视角排序：置顶优先，然后按最后消息时间（参与者视角），最后按会话更新时间
        query = query.order_by(
            desc(ConversationParticipant.is_pinned),  # 置顶的排前面
            desc(ConversationParticipant.pinned_at),  # 置顶时间倒序
            desc(ConversationParticipant.last_message_at),  # 个人最后消息时间倒序
            desc(Conversation.updated_at)  # 会话更新时间倒序
        )
        
        # 分页
        results = query.offset(skip).limit(limit).all()
        
        # 提取会话对象和参与者对象（因为查询返回的是 (Conversation, ConversationParticipant) 元组）
        conversations = []
        participants_dict = {}
        for conv, participant in results:
            conversations.append(conv)
            participants_dict[conv.id] = participant
        
        # 加载关联数据（owner 和 participants）
        conversation_ids = [conv.id for conv in conversations]
        if conversation_ids:
            # 批量加载关联数据
            conversations_with_relations = self.db.query(Conversation).options(
                joinedload(Conversation.owner),
                joinedload(Conversation.participants).joinedload(ConversationParticipant.user)
            ).filter(Conversation.id.in_(conversation_ids)).all()
            
            # 保持原有顺序
            conversation_dict = {conv.id: conv for conv in conversations_with_relations}
            conversations = [conversation_dict.get(conv.id, conv) for conv in conversations]
        
        # 批量获取每个会话的最后一条消息
        last_messages = {}
        if conversation_ids:
            # 为每个会话单独查询最后一条消息（更可靠，避免时间戳重复问题）
            for conv_id in conversation_ids:
                last_msg = self.db.query(Message).filter(
                    Message.conversation_id == conv_id
                ).order_by(
                    desc(Message.timestamp),
                    desc(Message.id)  # 如果时间戳相同，按ID倒序
                ).options(
                    joinedload(Message.sender)
                ).limit(1).first()
                
                if last_msg:
                    last_messages[conv_id] = last_msg
        
        # 转换为响应Schema
        conversation_infos = []
        for conv in conversations:
            participant = participants_dict.get(conv.id)
            last_message = last_messages.get(conv.id)
            last_message_info = MessageInfo.from_model(last_message) if last_message else None
            conv_info = ConversationInfo.from_model(
                conv,
                last_message=last_message_info,
                participant=participant
            )
            conversation_infos.append(conv_info)
        
        return PaginatedRecords(
            items=conversation_infos,
            total=total,
            skip=skip,
            limit=limit
        )
    
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
        participant = None
        if user_id:
            # 先查询会话是否存在
            conversation = query.first()
            if not conversation:
                return None
            
            # 检查用户是否是owner
            if str(conversation.owner_id) == user_id:
                # 是owner，获取或创建参与者记录
                participant = self._get_or_create_participant(conversation_id, user_id, default_role="owner")
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
        
        return ConversationInfo.from_model(conversation, last_message=last_message, participant=participant)
    
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
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            return None
        
        # 检查权限：用户必须是owner或参与者
        is_owner = str(conversation.owner_id) == user_id
        participant = self.db.query(ConversationParticipant).filter(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == user_id,
            ConversationParticipant.is_active == True
        ).first()
        
        if not is_owner and not participant:
            return None  # 无权限
        
        # 分离会话级别和个人级别的更新字段
        conversation_fields = ['title', 'is_active', 'is_archived', 'tag']
        participant_fields = ['is_pinned']
        
        # 更新会话级别字段（只有owner可以修改）
        if is_owner:
            for field, value in updates.items():
                if field in conversation_fields and hasattr(conversation, field):
                    setattr(conversation, field, value)
        
        # 获取或创建参与者记录（用于个人化字段）
        if not participant:
            participant = self._get_or_create_participant(conversation_id, user_id)
        
        # 更新个人化字段（所有参与者都可以修改自己的）
        if 'is_pinned' in updates:
            participant.is_pinned = updates['is_pinned']
            if updates['is_pinned']:
                participant.pinned_at = datetime.now()
            else:
                participant.pinned_at = None
        
        self.db.commit()
        self.db.refresh(conversation)
        self.db.refresh(participant)
        
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
        
        return ConversationInfo.from_model(conversation, last_message=last_message, participant=participant)
    
    # ============ 消息管理 ============
    
    def create_text_message(
        self,
        conversation_id: str,
        sender_id: str,
        content: str,
        sender_type: str = "user",
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
        
        # 更新所有参与者的统计信息
        self._update_participant_stats_on_new_message(conversation_id, sender_id)
        
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
        sender_type: str = "chat"
    ) -> MessageInfo:
        """创建媒体消息"""
        # 验证会话存在
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise BusinessException("会话不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
        
        # 构建符合前端 MediaMessageContent 接口的结构
        # export interface MediaMessageContent {
        #   text?: string;
        #   media_info: MediaInfo;
        # }
        content = {
            "type": "media",
            "text": text,
            "media_info": {
                "url": media_url,
                "name": "unknown",  # 简单创建模式下可能没有文件名
                "mime_type": f"{media_type}/*",  # 简单推断
                "size_bytes": 0,
                "metadata": {}
            }
        }
        
        # 创建消息
        message = Message(
            id=message_id(),
            conversation_id=conversation_id,
            content=content,
            type="media",
            sender_id=sender_id,
            sender_type=sender_type,
            is_read=False
        )
        
        self.db.add(message)
        
        # 更新所有参与者的统计信息
        self._update_participant_stats_on_new_message(conversation_id, sender_id)
        
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
        
        # 更新参与者的未读计数
        participant = self.db.query(ConversationParticipant).filter(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == user_id,
            ConversationParticipant.is_active == True
        ).first()
        
        if participant:
            participant.unread_count = max(0, (participant.unread_count or 0) - count)
            participant.last_read_at = datetime.now()
        
        self.db.commit()
        
        return count
    
    def mark_message_as_read_use_case(self, message_id: str, user_id: Optional[str] = None) -> bool:
        """标记消息为已读（用例方法）"""
        message = self.db.query(Message).filter(Message.id == message_id).first()
        if not message:
            return False
        
        message.is_read = True
        
        # 如果提供了user_id，更新该参与者的未读计数
        if user_id:
            participant = self.db.query(ConversationParticipant).filter(
                ConversationParticipant.conversation_id == message.conversation_id,
                ConversationParticipant.user_id == user_id,
                ConversationParticipant.is_active == True
            ).first()
            
            if participant:
                participant.unread_count = max(0, (participant.unread_count or 0) - 1)
                participant.last_read_at = datetime.now()
        
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
                sender_type="user",  # 智能聊天消息统一使用 user
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
                    sender_type="chat"  # 智能聊天消息统一使用chat
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
        return self.create_text_message(
            conversation_id=conversation_id,
            sender_id=str(sender.id),
            content=request.text,
            sender_type="user",  # 智能聊天消息统一使用 user
            reply_to_message_id=request.reply_to_message_id
        )
    
    def create_media_message_use_case(
        self,
        conversation_id: str,
        request: CreateMediaMessageRequest,
        sender: User
    ) -> MessageInfo:
        """创建媒体消息用例"""
        # 使用create_media_message_with_details方法，确保文件名和大小正确传递
        return self.create_media_message_with_details(
            conversation_id=conversation_id,
            sender_id=str(sender.id),
            media_url=request.media_url,
            media_name=request.media_name,  # 使用请求中的文件名
            mime_type=request.mime_type,  # 使用请求中的mime_type
            size_bytes=request.size_bytes,  # 使用请求中的文件大小
            text=request.text,
            metadata=request.metadata,
            is_important=request.is_important or False,
            upload_method=getattr(request, 'upload_method', None)
        )
    
    def create_system_event_message_use_case(
        self,
        conversation_id: str,
        request: CreateSystemEventRequest,
        sender: User
    ) -> MessageInfo:
        """创建系统事件消息用例"""
        # 权限检查：只有管理员可以创建系统事件消息
        from app.identity_access.deps.permission_deps import get_user_primary_role
        sender_role = get_user_primary_role(sender)
        if sender_role not in ["admin", "administrator", "super_admin"]:
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
        
        # 更新所有参与者的统计信息（系统消息不增加未读计数）
        self._update_participant_stats_on_new_message(conversation_id, "system", is_system_message=True)
        
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
            sender_type="user",  # 智能聊天消息统一使用 user
            is_read=False,
            extra_metadata=getattr(request, 'metadata', None)
        )
        
        self.db.add(message)
        
        # 更新所有参与者的统计信息
        self._update_participant_stats_on_new_message(conversation_id, str(sender.id))
        
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
        
        # 构建符合前端 MediaMessageContent 接口的结构
        # export interface MediaMessageContent {
        #   text?: string;
        #   media_info: MediaInfo;
        # }
        media_info = {
            "url": media_url,
            "name": media_name or "unknown",
            "mime_type": mime_type or "application/octet-stream",
            "size_bytes": size_bytes or 0,
            "metadata": metadata or {}
        }
        
        content = {
            "type": "media",
            "text": text,
            "media_info": media_info
        }
        
        # 创建消息
        message = Message(
            id=message_id(),
            conversation_id=conversation_id,
            content=content,
            type="media",
            sender_id=sender_id,
            sender_type="user",  # 智能聊天消息统一使用 user
            is_read=False,
            is_important=is_important
        )
        
        self.db.add(message)
        
        # 更新所有参与者的统计信息
        self._update_participant_stats_on_new_message(conversation_id, sender_id)
        
        self.db.commit()
        self.db.refresh(message)
        
        # 加载关联数据
        message = self.db.query(Message).options(
            joinedload(Message.sender)
        ).filter(Message.id == message.id).first()
        
        # 转换为响应Schema
        from app.chat.schemas.chat import MessageInfo
        return MessageInfo.from_model(message)
    
    # ============ 接管状态管理 ============
    
    def set_participant_takeover_status(
        self,
        conversation_id: str,
        user_id: str,
        takeover_status: str
    ) -> ConversationParticipant:
        """设置参与者的接管状态
        
        Args:
            conversation_id: 会话ID
            user_id: 用户ID
            takeover_status: 接管状态 ("full_takeover", "semi_takeover", "no_takeover")
        
        Returns:
            ConversationParticipant: 更新后的参与者记录
        """
        # 验证会话存在
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise BusinessException("会话不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
        
        # 验证接管状态值
        valid_statuses = ["full_takeover", "semi_takeover", "no_takeover"]
        if takeover_status not in valid_statuses:
            raise BusinessException(
                f"无效的接管状态: {takeover_status}，有效值: {valid_statuses}",
                code=ErrorCode.INVALID_INPUT
            )
        
        # 获取或创建参与者记录
        participant = self._get_or_create_participant(conversation_id, user_id)
        
        # 更新接管状态
        participant.takeover_status = takeover_status
        
        self.db.commit()
        self.db.refresh(participant)
        
        return participant
    
    def get_participant_takeover_status(
        self,
        conversation_id: str,
        user_id: str
    ) -> Optional[str]:
        """获取参与者的接管状态
        
        Args:
            conversation_id: 会话ID
            user_id: 用户ID
        
        Returns:
            Optional[str]: 接管状态，如果参与者不存在则返回None
        """
        participant = self.db.query(ConversationParticipant).filter(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == user_id,
            ConversationParticipant.is_active == True
        ).first()
        
        if not participant:
            return None
        
        return participant.takeover_status or "no_takeover"

