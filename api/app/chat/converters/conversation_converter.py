"""
会话转换器 - 遵循DDD转换器模式
负责领域实体与Schema之间的转换
"""
from typing import List, Optional, Dict
from app.chat.domain.entities.conversation import Conversation
from app.chat.domain.entities.message import Message
from app.chat.schemas.chat import ConversationInfo
from .message_converter import MessageConverter


class ConversationConverter:
    """会话转换器类"""
    
    @staticmethod
    def to_response(conversation: Conversation, last_message: Optional[Message] = None, unread_count: int = 0, sender_user=None, sender_digital_human=None) -> Optional[ConversationInfo]:
        """将领域实体转换为响应Schema"""
        if not conversation:
            return None
        
        # 手动构建ConversationInfo，不使用from_model
        return ConversationInfo(
            id=conversation.id,
            title=conversation.title,
            chat_mode=conversation.chat_mode,
            owner_id=conversation.owner_id,
            tag="chat",  # 默认值
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            is_active=conversation.is_active,
            is_archived=conversation.is_archived,
            is_pinned=conversation.is_pinned,
            pinned_at=conversation.pinned_at,
            first_participant_id=None,  # 需要从仓储获取
            message_count=conversation.message_count,
            unread_count=unread_count,
            last_message_at=conversation.last_message_at,
            owner=None,  # 需要从仓储获取
            first_participant=None,  # 需要从仓储获取
            last_message=MessageConverter.to_response(last_message, sender_user, sender_digital_human) if last_message else None
        )
    
    @staticmethod
    def to_list_response(conversations: List[Conversation], last_messages_with_senders: Optional[Dict[str, tuple]] = None, unread_counts: Optional[Dict[str, int]] = None) -> List[ConversationInfo]:
        """将领域实体列表转换为响应Schema列表"""
        if not last_messages_with_senders:
            last_messages_with_senders = {}
        if not unread_counts:
            unread_counts = {}
        
        result = []
        for conv in conversations:
            last_msg_data = last_messages_with_senders.get(str(conv.id))
            unread_count = unread_counts.get(str(conv.id), 0)
            
            # 解包元组数据
            last_msg = None
            sender_user = None
            sender_digital_human = None
            if last_msg_data:
                last_msg, sender_user, sender_digital_human = last_msg_data
            
            conv_info = ConversationConverter.to_response(
                conv, 
                last_msg, 
                unread_count,
                sender_user,
                sender_digital_human
            )
            if conv_info:
                result.append(conv_info)
        
        return result
    
    @staticmethod
    def from_schema(conversation_info: ConversationInfo) -> Conversation:
        """将Schema转换为领域实体（用于创建）"""
        from app.common.infrastructure.db.uuid_utils import conversation_id
        from datetime import datetime
        
        return Conversation(
            id=conversation_id(),
            title=conversation_info.title,
            chat_mode=getattr(conversation_info, 'chat_mode', 'single'),
            owner_id=conversation_info.owner_id,
            is_active=getattr(conversation_info, 'is_active', True),
            is_archived=getattr(conversation_info, 'is_archived', False),
            message_count=getattr(conversation_info, 'message_count', 0),
            unread_count=getattr(conversation_info, 'unread_count', 0),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )


