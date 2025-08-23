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
                logger.info(f"会话详情: id={conversation.id}, owner_id={conversation.owner_id}, assigned_consultant_id={conversation.assigned_consultant_id}")
            else:
                logger.warning(f"会话不存在: {conversation_id}")
            
            return False
        except Exception as e:
            logger.error(f"检查会话访问权限失败: {str(e)}", exc_info=True)
            return False

    def _validate_message_content(self, content: Dict[str, Any], message_type: str) -> None:
        """
        验证消息内容的有效性
        
        Args:
            content: 消息内容
            message_type: 消息类型
            
        Raises:
            ValueError: 内容验证失败时抛出
        """
        if content is None:
            raise ValueError("消息内容不能为空")
        
        if not isinstance(content, dict):
            raise ValueError("消息内容必须是对象")
        
        if len(content) == 0:
            if message_type == "system":
                raise ValueError("系统事件消息内容不能为空")
        
        # 验证特定类型的必需字段和字段一致性
        if message_type == "text":
            if "text" not in content:
                raise ValueError("文本消息必须包含text字段")
            # 检查是否包含不应该出现的字段
            invalid_fields = set(content.keys()) - {"text"}
            if invalid_fields:
                raise ValueError(f"文本消息包含无效字段: {', '.join(invalid_fields)}")
        elif message_type == "media":
            if "media_info" not in content:
                raise ValueError("媒体消息必须包含media_info字段")
            # 验证media_info结构
            media_info = content["media_info"]
            if not isinstance(media_info, dict):
                raise ValueError("media_info必须是对象")
            required_fields = ["url", "name", "mime_type", "size_bytes"]
            for field in required_fields:
                if field not in media_info:
                    raise ValueError(f"media_info缺少必需字段: {field}")
            # 检查是否包含不应该出现的字段（除了text和media_info）
            invalid_fields = set(content.keys()) - {"text", "media_info"}
            if invalid_fields:
                raise ValueError(f"媒体消息包含无效字段: {', '.join(invalid_fields)}")
        elif message_type == "system":
            if "system_event_type" not in content and "event_type" not in content:
                raise ValueError("系统事件消息必须包含system_event_type或event_type字段")
        elif message_type == "structured":
            required_fields = ["card_type", "title"]
            for field in required_fields:
                if field not in content:
                    raise ValueError(f"结构化消息缺少必需字段: {field}")

    def create_message(
        self,
        conversation_id: str,
        content: Dict[str, Any],
        message_type: str,
        sender_id: Optional[str] = None,
        sender_digital_human_id: Optional[str] = None,
        sender_type: str = "user",
        is_important: bool = False,
        reply_to_message_id: Optional[str] = None,
        reactions: Optional[Dict[str, List[str]]] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
        requires_confirmation: bool = False
    ) -> Message:
        """
        创建新消息
        
        Args:
            conversation_id: 会话ID
            sender_id: 发送者ID
            sender_type: 发送者类型
            content: 结构化消息内容
            message_type: 消息类型 (text, media, system, structured)
            is_important: 是否重要
            reply_to_message_id: 回复的消息ID
            reactions: 消息反应
            extra_metadata: 额外元数据
            
        Returns:
            创建的消息实例
        """
        # 验证消息内容
        self._validate_message_content(content, message_type)
        
        # 调试日志：记录保存前的内容
        logger.info(f"创建消息 - 保存前内容: conversation_id={conversation_id}, type={message_type}, content={content}")
        
        message = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            sender_digital_human_id=sender_digital_human_id,
            sender_type=sender_type,
            content=content,
            type=message_type,
            is_important=is_important,
            reply_to_message_id=reply_to_message_id,
            reactions=reactions,
            extra_metadata=extra_metadata,
            requires_confirmation=requires_confirmation,
            is_confirmed=not requires_confirmation  # 如果需要确认则默认未确认
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        # 调试日志：记录保存后的内容
        logger.info(f"创建消息 - 保存后内容: message_id={message.id}, content={message.content}")
        
        return message

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
    ) -> Message:
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
            创建的消息实例
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

    def create_media_message(
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
    ) -> Message:
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
            创建的消息实例
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
        
        return self.create_message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            sender_type=sender_type,
            content=content,
            message_type="media",
            is_important=is_important,
            reply_to_message_id=reply_to_message_id,
            extra_metadata=extra_metadata
        )

    def create_system_event_message(
        self,
        conversation_id: str,
        event_type: str,
        status: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None
    ) -> Message:
        """
        创建系统事件消息的便利方法
        
        Args:
            conversation_id: 会话ID
            event_type: 事件类型
            status: 事件状态
            event_data: 事件数据
            
        Returns:
            创建的消息实例
        """
        content = create_system_event_content(
            event_type=event_type,
            status=status,
            **(event_data or {})
        )
        
        return self.create_message(
            conversation_id=conversation_id,
            sender_id="system",
            sender_type="system",
            content=content,
            message_type="system"
        )

    def create_appointment_card_message(
        self,
        conversation_id: str,
        sender_id: str,
        sender_type: str,
        appointment_data: AppointmentCardData,
        title: str = "预约确认",
        subtitle: Optional[str] = None
    ) -> Message:
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
            创建的消息实例
        """
        content = create_appointment_card_content(
            appointment_data=appointment_data,
            title=title,
            subtitle=subtitle
        )
        
        return self.create_message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            sender_type=sender_type,
            content=content,
            message_type="structured",
            is_important=True  # 预约消息通常标记为重要
        )

    def create_service_recommendation_message(
        self,
        conversation_id: str,
        sender_id: str,
        sender_type: str,
        services: List[Dict[str, Any]],
        title: str = "推荐服务"
    ) -> Message:
        """
        创建服务推荐卡片消息
        
        Args:
            conversation_id: 会话ID
            sender_id: 发送者ID
            sender_type: 发送者类型
            services: 推荐服务列表
            title: 卡片标题
            
        Returns:
            创建的消息实例
        """
        content = create_service_recommendation_content(
            services=services,
            title=title
        )
        
        return self.create_message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            sender_type=sender_type,
            content=content,
            message_type="structured"
        )

    def create_custom_structured_message(
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
    ) -> Message:
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
            创建的消息实例
        """
        content = {
            "card_type": card_type,
            "title": title,
            "subtitle": subtitle,
            "data": data,
            "components": components,
            "actions": actions
        }
        
        return self.create_message(
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
        
        # 更新已读状态
        message.is_read = True
        
        self.db.commit()
        
        logger.info(f"消息已标记为已读: message_id={message_id}")
        return True
    
    def get_unread_message_count(self, conversation_id: str, user_id: str) -> int:
        """获取用户在会话中的未读消息数"""
        count = self.db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.sender_id != user_id,  # 不包括自己发送的消息
            Message.is_read == False
        ).count()
        
        return count
    
    def get_recent_messages(
        self,
        conversation_id: str,
        limit: int = 10
    ) -> List[MessageInfo]:
        """获取最近的消息（用于AI上下文）"""
        messages = self.db.query(Message).options(
            joinedload(Message.sender)
        ).filter(
            Message.conversation_id == conversation_id
        ).order_by(
            Message.timestamp.desc()
        ).limit(limit).all()
        
        # 返回时间正序的消息
        return [MessageInfo.from_model(msg) for msg in reversed(messages)]
    
    def delete_message(self, message_id: str, user_id: str) -> bool:
        """删除消息（软删除）"""
        message = self.db.query(Message).filter(
            Message.id == message_id,
            Message.sender_id == user_id  # 只能删除自己的消息
        ).first()
        
        if not message:
            return False
        
        # 软删除：标记为已删除而不是真正删除
        message.is_deleted = True
        message.deleted_at = datetime.now()
        
        self.db.commit()
        
        logger.info(f"消息已删除: message_id={message_id}, user_id={user_id}")
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
        
        # 更新重点状态
        message.is_important = is_important
        
        self.db.commit()
        
        logger.info(f"消息重点状态已更新: message_id={message_id}, is_important={is_important}")
        return True 