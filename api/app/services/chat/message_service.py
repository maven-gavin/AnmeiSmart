"""
聊天消息服务层
负责处理消息的创建、更新和查询逻辑

支持统一消息模型的四种类型：
- text: 纯文本消息
- media: 媒体文件消息
- system: 系统事件消息  
- structured: 结构化卡片消息
"""
from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from datetime import datetime
import logging
import json

from app.db.models.chat import Message, Conversation
from app.db.models.user import User
from app.db.uuid_utils import message_id
from app.schemas.chat import (
    MessageCreate, MessageInfo, 
    TextMessageContent, MediaMessageContent, SystemEventContent,
    create_text_message_content, create_media_message_content, create_system_event_content,
    create_appointment_card_content,
    create_service_recommendation_content,
    AppointmentCardData
)
from app.core.events import event_bus, EventTypes, create_message_event

logger = logging.getLogger(__name__)


class MessageService:
    """消息服务类，提供消息相关的业务逻辑"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def can_access_conversation(self, conversation_id: str, user_id: str) -> bool:
        """
        检查用户是否有权限访问会话
        
        Args:
            conversation_id: 会话ID
            user_id: 用户ID
            
        Returns:
            是否有权限
        """
        try:
            logger.info(f"开始检查会话访问权限: conversation_id={conversation_id}, user_id={user_id}")
            
            # 查询会话是否存在且用户有访问权限
            # 使用新的owner_id字段
            conversation = self.db.query(Conversation).filter(
                and_(
                    Conversation.id == conversation_id,
                    Conversation.owner_id == user_id
                )
            ).first()
            
            logger.info(f"查询作为会话所有者的会话: found={conversation is not None}")
            if conversation:
                logger.info(f"会话 {conversation_id} 的所有者ID: {conversation.owner_id}, 匹配用户ID: {user_id}")
                return True
            
            # 检查用户是否是会话参与者
            from app.db.models.chat import ConversationParticipant
            participant = self.db.query(ConversationParticipant).filter(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.user_id == user_id,
                    ConversationParticipant.is_active == True
                )
            ).first()
            
            logger.info(f"查询作为参与者的会话: found={participant is not None}")
            if participant:
                logger.info(f"用户 {user_id} 是会话 {conversation_id} 的参与者")
                return True
            
            # 检查用户是否是管理员或其他特殊角色
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                user_role_names = [role.name for role in user.roles]
                logger.info(f"用户 {user_id} 的角色: {user_role_names}")
                if any(role_name in ['admin', 'operator'] for role_name in user_role_names):
                    # 管理员和运营人员可以访问所有会话
                    conversation = self.db.query(Conversation).filter(
                        Conversation.id == conversation_id
                    ).first()
                    logger.info(f"管理员用户访问会话: conversation_exists={conversation is not None}")
                    return conversation is not None
            else:
                logger.warning(f"找不到用户: {user_id}")
            
            # 最后检查会话是否存在并打印详细信息
            conversation = self.db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            
            if conversation:
                logger.warning(f"会话存在但用户无权访问: conversation_id={conversation_id}, owner_id={conversation.owner_id}, user_id={user_id}")
            else:
                logger.warning(f"会话不存在: conversation_id={conversation_id}")
            
            return False
            
        except Exception as e:
            logger.error(f"检查会话访问权限时出错: {e}")
            return False

    async def create_message(
        self,
        conversation_id: str,
        content: Union[str, Dict[str, Any]],
        message_type: str,
        sender_id: Optional[str] = None,
        sender_digital_human_id: Optional[str] = None,
        sender_type: str = "user",
        is_important: bool = False,
        reply_to_message_id: Optional[str] = None,
        reactions: Optional[Dict[str, List[str]]] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
        requires_confirmation: bool = False
    ) -> MessageInfo:
        """
        创建消息的通用方法
        
        Args:
            conversation_id: 会话ID
            content: 消息内容（字符串或结构化字典）
            message_type: 消息类型 (text, media, system, structured)
            sender_id: 发送者ID
            sender_digital_human_id: 数字人发送者ID
            sender_type: 发送者类型
            is_important: 是否重要
            reply_to_message_id: 回复的消息ID
            reactions: 反应数据
            extra_metadata: 额外元数据
            requires_confirmation: 是否需要确认
            
        Returns:
            创建的消息信息
        """
        # 验证会话存在
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise ValueError(f"会话不存在: {conversation_id}")
        
        # 确保content是字典格式
        if isinstance(content, str):
            content = {"text": content}
        
        # 调试日志：记录保存前的内容
        logger.debug(f"创建消息: conversation_id={conversation_id}, type={message_type}, content={json.dumps(content, ensure_ascii=False)}")
        
        # 创建消息实例
        message = Message(
            id=message_id(),
            conversation_id=conversation_id,
            sender_id=sender_id,
            sender_digital_human_id=sender_digital_human_id,
            sender_type=sender_type,
            content=content,
            type=message_type,
            is_important=is_important,
            reply_to_message_id=reply_to_message_id,
            reactions=reactions or {},
            extra_metadata=extra_metadata or {},
            requires_confirmation=requires_confirmation,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        logger.info(f"消息创建成功: id={message.id}, type={message_type}")
        
        # 发布消息事件（异步处理）
        try:
            event = create_message_event(
                conversation_id=conversation_id,
                user_id=sender_id or "system",
                content=json.dumps(content, ensure_ascii=False),
                message_type=message_type,
                sender_type=sender_type
            )
            # 使用asyncio.create_task避免阻塞
            import asyncio
            asyncio.create_task(event_bus.publish_async(event))
        except Exception as e:
            logger.warning(f"发布消息事件失败: {e}")
        
        # 返回schema对象而不是ORM对象
        return MessageInfo.from_model(message)

    def create_text_message(
        self,
        conversation_id: str,
        text: str,
        sender_id: Optional[str] = None,
        sender_digital_human_id: Optional[str] = None,
        sender_type: str = "user",
        is_important: bool = False,
        reply_to_message_id: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
        requires_confirmation: bool = False
    ) -> MessageInfo:
        """
        创建文本消息的便利方法
        
        Args:
            conversation_id: 会话ID
            sender_id: 发送者ID  
            sender_type: 发送者类型
            text: 文本内容
            is_important: 是否重要
            reply_to_message_id: 回复的消息ID
            extra_metadata: 额外元数据
            
        Returns:
            创建的消息信息
        """
        content = create_text_message_content(text)
        
        return self.create_message(
            conversation_id=conversation_id,
            content=content,
            message_type="text",
            sender_id=sender_id,
            sender_digital_human_id=sender_digital_human_id,
            sender_type=sender_type,
            is_important=is_important,
            reply_to_message_id=reply_to_message_id,
            extra_metadata=extra_metadata,
            requires_confirmation=requires_confirmation
        )

    async def create_media_message(
        self,
        conversation_id: str,
        sender_id: str,
        sender_type: str,
        media_url: str,
        media_name: str,
        mime_type: str,
        size_bytes: int,
        text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        is_important: bool = False,
        reply_to_message_id: Optional[str] = None,
        upload_method: Optional[str] = None
    ) -> MessageInfo:
        """
        创建媒体消息的便利方法
        
        Args:
            conversation_id: 会话ID
            sender_id: 发送者ID
            sender_type: 发送者类型
            media_url: 媒体文件URL
            media_name: 媒体文件名
            mime_type: MIME类型
            size_bytes: 文件大小
            text: 附带文字（可选）
            metadata: 媒体元数据（如宽高、时长等）
            is_important: 是否重要
            reply_to_message_id: 回复的消息ID
            upload_method: 上传方式
            
        Returns:
            创建的消息信息
        """
        content = create_media_message_content(
            media_url=media_url,
            media_name=media_name,
            mime_type=mime_type,
            size_bytes=size_bytes,
            text=text,
            metadata=metadata
        )
        
        # 将上传方式添加到额外元数据中
        extra_metadata = {"upload_method": upload_method} if upload_method else None
        
        return await self.create_message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            sender_type=sender_type,
            content=content,
            message_type="media",
            is_important=is_important,
            reply_to_message_id=reply_to_message_id,
            extra_metadata=extra_metadata
        )

    async def create_system_event_message(
        self,
        conversation_id: str,
        event_type: str,
        status: Optional[str] = None,
        sender_id: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None
    ) -> MessageInfo:
        """
        创建系统事件消息的便利方法
        
        Args:
            conversation_id: 会话ID
            event_type: 事件类型
            status: 事件状态
            sender_id: 发送者ID
            event_data: 事件数据
            
        Returns:
            创建的消息信息
        """
        content = create_system_event_content(
            event_type=event_type,
            status=status,
            **(event_data or {})
        )
        
        return await self.create_message(
            conversation_id=conversation_id,
            sender_id=sender_id or "system",
            sender_type="system",
            content=content,
            message_type="system"
        )

    async def create_appointment_card_message(
        self,
        conversation_id: str,
        sender_id: str,
        sender_type: str,
        appointment_data: AppointmentCardData,
        title: str = "预约确认",
        subtitle: Optional[str] = None
    ) -> MessageInfo:
        """
        创建预约确认卡片消息
        
        Args:
            conversation_id: 会话ID
            sender_id: 发送者ID
            sender_type: 发送者类型
            appointment_data: 预约数据
            title: 卡片标题
            subtitle: 卡片副标题
            
        Returns:
            创建的消息信息
        """
        content = create_appointment_card_content(
            appointment_data=appointment_data,
            title=title,
            subtitle=subtitle
        )
        
        return await self.create_message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            sender_type=sender_type,
            content=content,
            message_type="structured",
            is_important=True  # 预约消息通常标记为重要
        )

    async def create_service_recommendation_message(
        self,
        conversation_id: str,
        sender_id: str,
        sender_type: str,
        services: List[Dict[str, Any]],
        title: str = "推荐服务"
    ) -> MessageInfo:
        """
        创建服务推荐卡片消息
        
        Args:
            conversation_id: 会话ID
            sender_id: 发送者ID
            sender_type: 发送者类型
            services: 推荐服务列表
            title: 卡片标题
            
        Returns:
            创建的消息信息
        """
        content = create_service_recommendation_content(
            services=services,
            title=title
        )
        
        return await self.create_message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            sender_type=sender_type,
            content=content,
            message_type="structured"
        )

    async def create_custom_structured_message(
        self,
        conversation_id: str,
        sender_id: str,
        sender_type: str,
        card_type: str,
        title: str,
        data: Dict[str, Any],
        subtitle: Optional[str] = None,
        components: Optional[List[Dict[str, Any]]] = None,
        actions: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> MessageInfo:
        """
        创建自定义结构化消息
        
        Args:
            conversation_id: 会话ID
            sender_id: 发送者ID
            sender_type: 发送者类型
            card_type: 卡片类型
            title: 卡片标题
            data: 卡片数据
            subtitle: 卡片副标题
            components: 卡片组件
            actions: 卡片操作
            
        Returns:
            创建的消息信息
        """
        content = {
            "card_type": card_type,
            "title": title,
            "subtitle": subtitle,
            "data": data,
            "components": components,
            "actions": actions
        }
        
        return await self.create_message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            sender_type=sender_type,
            content=content,
            message_type="structured"
        )

    def get_conversation_messages(
        self,
        conversation_id: str,
        skip: int = 0,
        limit: int = 100,
        order_desc: bool = False
    ) -> List[MessageInfo]:
        """获取会话消息"""
        logger.debug(f"获取会话消息: conversation_id={conversation_id}, skip={skip}, limit={limit}")
        
        query = self.db.query(Message).options(
            joinedload(Message.sender)
        ).filter(
            Message.conversation_id == conversation_id
        )
        
        if order_desc:
            query = query.order_by(Message.timestamp.desc())
        else:
            query = query.order_by(Message.timestamp)
        
        messages = query.offset(skip).limit(limit).all()
        
        logger.debug(f"查询到 {len(messages)} 条消息")
        return [MessageInfo.from_model(msg) for msg in messages]
    
    def get_message_by_id(self, message_id: str) -> Optional[MessageInfo]:
        """根据ID获取消息"""
        message = self.db.query(Message).options(
            joinedload(Message.sender)
        ).filter(Message.id == message_id).first()
        return MessageInfo.from_model(message) if message else None
    
    def mark_messages_as_read(self, message_ids: List[str], user_id: str) -> int:
        """标记消息为已读"""
        logger.info(f"标记消息已读: message_ids={message_ids}, user_id={user_id}")
        
        updated_count = self.db.query(Message).filter(
            Message.id.in_(message_ids)
        ).update(
            {"is_read": True},
            synchronize_session=False
        )
        
        self.db.commit()
        
        logger.info(f"已标记 {updated_count} 条消息为已读")
        return updated_count
    
    def mark_message_as_read(self, message_id: str) -> bool:
        """标记单个消息为已读"""
        logger.info(f"标记单个消息已读: message_id={message_id}")
        
        message = self.db.query(Message).filter(
            Message.id == message_id
        ).first()
        
        if not message:
            logger.warning(f"消息不存在: message_id={message_id}")
            return False
        
        message.is_read = True
        message.updated_at = datetime.now()
        self.db.commit()
        
        logger.info(f"消息已标记为已读: message_id={message_id}")
        return True
    
    def mark_message_as_important(self, message_id: str, is_important: bool) -> bool:
        """标记消息为重点"""
        logger.info(f"标记消息重点状态: message_id={message_id}, is_important={is_important}")
        
        message = self.db.query(Message).filter(
            Message.id == message_id
        ).first()
        
        if not message:
            logger.warning(f"消息不存在: message_id={message_id}")
            return False
        
        message.is_important = is_important
        message.updated_at = datetime.now()
        self.db.commit()
        
        logger.info(f"消息重点状态已更新: message_id={message_id}, is_important={is_important}")
        return True
    
    def get_recent_messages(self, conversation_id: str, limit: int = 10) -> List[MessageInfo]:
        """获取最近的消息"""
        messages = self.db.query(Message).options(
            joinedload(Message.sender)
        ).filter(
            Message.conversation_id == conversation_id
        ).order_by(
            Message.timestamp.desc()
        ).limit(limit).all()
        
        # 按时间正序返回
        messages.reverse()
        return [MessageInfo.from_model(msg) for msg in messages]
    
    def search_messages(
        self,
        conversation_id: str,
        query: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[MessageInfo]:
        """搜索消息"""
        # 简单的文本搜索，可以根据需要扩展
        messages = self.db.query(Message).options(
            joinedload(Message.sender)
        ).filter(
            Message.conversation_id == conversation_id,
            Message.content.contains(query)
        ).order_by(
            Message.timestamp.desc()
        ).offset(skip).limit(limit).all()
        
        return [MessageInfo.from_model(msg) for msg in messages]
    
    def delete_message(self, message_id: str, user_id: str) -> bool:
        """删除消息（软删除）"""
        logger.info(f"删除消息: message_id={message_id}, user_id={user_id}")
        
        message = self.db.query(Message).filter(
            Message.id == message_id
        ).first()
        
        if not message:
            logger.warning(f"消息不存在: message_id={message_id}")
            return False
        
        # 检查权限：只有发送者或管理员可以删除
        if str(message.sender_id) != user_id:
            # 检查用户是否是管理员
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user or not any(role.name in ['admin', 'operator'] for role in user.roles):
                logger.warning(f"用户无权删除消息: user_id={user_id}, message_sender_id={message.sender_id}")
                return False
        
        # 软删除：标记为已删除
        message.is_deleted = True
        message.deleted_at = datetime.now()
        message.deleted_by = user_id
        message.updated_at = datetime.now()
        
        self.db.commit()
        
        logger.info(f"消息已删除: message_id={message_id}")
        return True
    
    def add_reaction_to_message(self, message_id: str, user_id: str, emoji: str) -> bool:
        """为消息添加反应"""
        logger.info(f"添加消息反应: message_id={message_id}, user_id={user_id}, emoji={emoji}")
        
        message = self.db.query(Message).filter(
            Message.id == message_id
        ).first()
        
        if not message:
            logger.warning(f"消息不存在: message_id={message_id}")
            return False
        
        # 初始化反应数据
        if not message.reactions:
            message.reactions = {}
        
        # 添加反应
        if emoji not in message.reactions:
            message.reactions[emoji] = []
        
        if user_id not in message.reactions[emoji]:
            message.reactions[emoji].append(user_id)
            message.updated_at = datetime.now()
            self.db.commit()
            
            logger.info(f"反应添加成功: message_id={message_id}, emoji={emoji}")
            return True
        
        logger.info(f"用户已添加过此反应: message_id={message_id}, user_id={user_id}, emoji={emoji}")
        return False
    
    def remove_reaction_from_message(self, message_id: str, user_id: str, emoji: str) -> bool:
        """移除消息的反应"""
        logger.info(f"移除消息反应: message_id={message_id}, user_id={user_id}, emoji={emoji}")
        
        message = self.db.query(Message).filter(
            Message.id == message_id
        ).first()
        
        if not message:
            logger.warning(f"消息不存在: message_id={message_id}")
            return False
        
        # 移除反应
        if message.reactions and emoji in message.reactions:
            if user_id in message.reactions[emoji]:
                message.reactions[emoji].remove(user_id)
                
                # 如果没有用户使用此反应，删除整个反应
                if not message.reactions[emoji]:
                    del message.reactions[emoji]
                
                message.updated_at = datetime.now()
                self.db.commit()
                
                logger.info(f"反应移除成功: message_id={message_id}, emoji={emoji}")
                return True
        
        logger.info(f"用户未添加过此反应: message_id={message_id}, user_id={user_id}, emoji={emoji}")
        return False 