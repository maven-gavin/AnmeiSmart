"""
消息服务 - 处理消息的创建、存储和查询
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.db.models.chat import Message, Conversation
from app.db.models.user import User
from app.db.uuid_utils import message_id
from app.schemas.chat import MessageCreate
from app.core.events import event_bus, EventTypes, create_message_event

logger = logging.getLogger(__name__)


class MessageService:
    """消息服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_message(
        self,
        conversation_id: str,
        content: str,
        message_type: str,
        sender_id: str,
        sender_type: str,
        is_important: bool = False
    ) -> Message:
        """创建新消息"""
        logger.info(f"创建消息: conversation_id={conversation_id}, sender_id={sender_id}")
        
        # 验证会话存在
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise ValueError(f"会话不存在: {conversation_id}")
        
        # 创建消息
        new_message = Message(
            id=message_id(),
            conversation_id=conversation_id,
            content=content,
            type=message_type,
            sender_id=sender_id,
            sender_type=sender_type,
            is_read=False,
            is_important=is_important,
            timestamp=datetime.now()
        )
        
        self.db.add(new_message)
        
        # 更新会话最后更新时间
        conversation.updated_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(new_message)
        
        logger.info(f"消息创建成功: message_id={new_message.id}")
        
        # 发布消息创建事件
        event = create_message_event(
            conversation_id=conversation_id,
            user_id=sender_id,
            content=content,
            message_type=message_type,
            sender_type=sender_type,
            is_important=is_important,
            message_id=new_message.id
        )
        await event_bus.publish_async(event)
        
        return new_message
    
    def get_conversation_messages(
        self,
        conversation_id: str,
        skip: int = 0,
        limit: int = 100,
        order_desc: bool = False
    ) -> List[Message]:
        """获取会话消息"""
        logger.debug(f"获取会话消息: conversation_id={conversation_id}, skip={skip}, limit={limit}")
        
        query = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        )
        
        if order_desc:
            query = query.order_by(Message.timestamp.desc())
        else:
            query = query.order_by(Message.timestamp)
        
        messages = query.offset(skip).limit(limit).all()
        
        logger.debug(f"查询到 {len(messages)} 条消息")
        return messages
    
    def get_message_by_id(self, message_id: str) -> Optional[Message]:
        """根据ID获取消息"""
        return self.db.query(Message).filter(Message.id == message_id).first()
    
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
    ) -> List[Message]:
        """获取最近的消息（用于AI上下文）"""
        messages = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(
            Message.timestamp.desc()
        ).limit(limit).all()
        
        # 返回时间正序的消息
        return list(reversed(messages))
    
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
    
    def convert_to_schema(self, message: Message) -> Dict[str, Any]:
        """将消息模型转换为API响应格式"""
        if not message:
            return None
        
        # 获取发送者信息
        sender_info = {
            "id": message.sender_id or "system",
            "name": "系统" if message.sender_type == "system" else "AI助手" if message.sender_type == "ai" else "未知用户",
            "avatar": None,
            "type": message.sender_type
        }
        
        # 如果有发送者关联对象，使用真实信息
        if message.sender:
            sender_info.update({
                "name": message.sender.username,
                "avatar": message.sender.avatar
            })
        
        return {
            "id": message.id,
            "conversation_id": message.conversation_id,
            "content": message.content,
            "type": message.type,
            "sender": sender_info,
            "timestamp": message.timestamp,
            "is_read": message.is_read,
            "is_important": message.is_important
        } 