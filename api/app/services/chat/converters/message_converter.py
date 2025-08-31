"""
消息转换器 - 遵循DDD转换器模式
负责领域实体与Schema之间的转换
"""
from typing import List, Optional, Literal
from app.services.chat.domain.entities.message import Message
from app.schemas.chat import MessageInfo, MessageSender


class MessageConverter:
    """消息转换器类"""
    
    @staticmethod
    def to_response(message: Message, sender_user=None, sender_digital_human=None) -> Optional[MessageInfo]:
        """将领域实体转换为响应Schema"""
        if not message:
            return None
        
        # 构建sender对象
        sender_name = "系统"
        sender_avatar = None
        actual_sender_id = "system"
        
        if message.sender_type == "system":
            sender_name = "系统"
            sender_avatar = "/avatars/system.png"
            actual_sender_id = "system"
        elif message.sender_type == "digital_human":
            sender_name = "数字人助手"
            sender_avatar = "/avatars/ai.png"
            actual_sender_id = message.sender_digital_human_id or "digital_human"
            # 如果有数字人信息，使用真实名称
            if sender_digital_human:
                sender_name = getattr(sender_digital_human, 'name', sender_name)
                sender_avatar = getattr(sender_digital_human, 'avatar', sender_avatar)
        elif message.sender_type == "ai":
            sender_name = "AI助手"
            sender_avatar = "/avatars/ai.png"
            actual_sender_id = message.sender_id or "ai"
        else:
            # 用户类型（customer, consultant, doctor等）
            sender_name = "未知用户"
            sender_avatar = None
            actual_sender_id = message.sender_id or "unknown"
            # 如果有用户信息，使用真实用户名
            if sender_user:
                sender_name = getattr(sender_user, 'username', sender_name)
                sender_avatar = getattr(sender_user, 'avatar', sender_avatar)
        
        # 确保sender_type是有效的Literal类型
        sender_type: Literal["customer", "consultant", "doctor", "ai", "system", "digital_human"] = "system"
        if message.sender_type in ["customer", "consultant", "doctor", "ai", "system", "digital_human"]:
            sender_type = message.sender_type  # type: ignore
        
        sender = MessageSender(
            id=actual_sender_id,
            name=sender_name,
            avatar=sender_avatar,
            type=sender_type
        )
        
        # 确保message_type是有效的Literal类型
        message_type: Literal["text", "media", "system", "structured"] = "text"
        if message.message_type in ["text", "media", "system", "structured"]:
            message_type = message.message_type  # type: ignore
        
        # 手动构建MessageInfo，不使用from_model
        return MessageInfo(
            id=message.id,
            conversation_id=message.conversation_id,
            sender=sender,
            content=message.content,
            type=message_type,
            timestamp=message.created_at,
            is_read=message.is_read,
            is_important=message.is_important,
            reply_to_message_id=message.reply_to_message_id,
            reactions=message.reactions,
            extra_metadata=message.extra_metadata
        )
    
    @staticmethod
    def to_list_response(messages: List[Message], sender_users: dict = None, sender_digital_humans: dict = None) -> List[MessageInfo]:
        """将领域实体列表转换为响应Schema列表"""
        result = []
        for msg in messages:
            if msg:
                # 获取对应的用户信息
                sender_user = None
                sender_digital_human = None
                
                if sender_users and msg.sender_id:
                    sender_user = sender_users.get(msg.sender_id)
                if sender_digital_humans and msg.sender_digital_human_id:
                    sender_digital_human = sender_digital_humans.get(msg.sender_digital_human_id)
                
                converted = MessageConverter.to_response(msg, sender_user, sender_digital_human)
                if converted:
                    result.append(converted)
        return result
    
    @staticmethod
    def from_schema(message_info: MessageInfo) -> Message:
        """将Schema转换为领域实体（用于创建）"""
        from app.db.uuid_utils import message_id
        from datetime import datetime
        
        return Message(
            id=message_id(),
            conversation_id=message_info.conversation_id,
            content=message_info.content,
            message_type=message_info.type,
            sender_id=message_info.sender.id if message_info.sender else None,
            sender_type=message_info.sender.type if message_info.sender else "user",
            is_important=message_info.is_important,
            reply_to_message_id=message_info.reply_to_message_id,
            reactions=message_info.reactions or {},
            extra_metadata=message_info.extra_metadata or {},
            requires_confirmation=False,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
