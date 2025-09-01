"""
消息仓储 - 基础设施层
负责消息数据持久化，技术实现
遵循DDD分层架构的基础设施层职责
"""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
import logging
from datetime import datetime

from app.chat.infrastructure.db.chat import Message as MessageModel
from app.chat.domain.interfaces import IMessageRepository
from app.chat.domain.entities.message import Message

logger = logging.getLogger(__name__)


class MessageRepository(IMessageRepository):
    """消息仓储实现 - 基础设施层"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _to_entity(self, model: MessageModel) -> Message:
        """ORM模型转领域实体"""
        return Message(
            id=str(model.id),
            conversation_id=str(model.conversation_id),
            content=model.content,
            message_type=model.type,
            sender_id=str(model.sender_id) if model.sender_id else None,
            sender_digital_human_id=str(model.sender_digital_human_id) if model.sender_digital_human_id else None,
            sender_type=model.sender_type,
            is_important=model.is_important,
            reply_to_message_id=str(model.reply_to_message_id) if model.reply_to_message_id else None,
            reactions=model.reactions,
            extra_metadata=model.extra_metadata,
            requires_confirmation=model.requires_confirmation,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _to_model(self, entity: Message) -> MessageModel:
        """领域实体转ORM模型"""
        return MessageModel(
            id=entity.id,
            conversation_id=entity.conversation_id,
            content=entity.content,
            type=entity.message_type,
            sender_id=entity.sender_id,
            sender_digital_human_id=entity.sender_digital_human_id,
            sender_type=entity.sender_type,
            is_important=entity.is_important,
            reply_to_message_id=entity.reply_to_message_id,
            reactions=entity.reactions,
            extra_metadata=entity.extra_metadata,
            requires_confirmation=entity.requires_confirmation,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
    
    async def save(self, message: Message) -> Message:
        """保存消息"""
        message_model = self._to_model(message)
        self.db.add(message_model)
        self.db.commit()
        self.db.refresh(message_model)
        
        # 更新实体的时间戳
        message._updated_at = message_model.updated_at
        
        logger.info(f"消息保存成功: id={message.id}")
        return message
    
    async def get_by_id(self, message_id: str) -> Optional[Message]:
        """根据ID获取消息"""
        message_model = self.db.query(MessageModel).options(
            joinedload(MessageModel.sender)
        ).filter(MessageModel.id == message_id).first()
        
        if not message_model:
            return None
        
        return self._to_entity(message_model)
    
    async def get_conversation_messages(self, conversation_id: str, skip: int = 0, limit: int = 100) -> List[Message]:
        """获取会话消息"""
        message_models = self.db.query(MessageModel).options(
            joinedload(MessageModel.sender),
            joinedload(MessageModel.sender_digital_human)
        ).filter(
            MessageModel.conversation_id == conversation_id
        ).order_by(
            MessageModel.timestamp
        ).offset(skip).limit(limit).all()
        
        return [self._to_entity(msg) for msg in message_models]
    
    async def get_conversation_messages_with_senders(self, conversation_id: str, skip: int = 0, limit: int = 100) -> tuple[List[Message], dict, dict]:
        """获取会话消息及发送者信息"""
        message_models = self.db.query(MessageModel).options(
            joinedload(MessageModel.sender),
            joinedload(MessageModel.sender_digital_human)
        ).filter(
            MessageModel.conversation_id == conversation_id
        ).order_by(
            MessageModel.timestamp
        ).offset(skip).limit(limit).all()
        
        # 转换为领域实体
        messages = [self._to_entity(msg) for msg in message_models]
        
        # 构建发送者信息字典
        sender_users = {}
        sender_digital_humans = {}
        
        for msg_model in message_models:
            if msg_model.sender and msg_model.sender_id:
                sender_users[str(msg_model.sender_id)] = msg_model.sender
            if msg_model.sender_digital_human and msg_model.sender_digital_human_id:
                sender_digital_humans[str(msg_model.sender_digital_human_id)] = msg_model.sender_digital_human
        
        return messages, sender_users, sender_digital_humans
    
    async def mark_as_read(self, message_id: str) -> bool:
        """标记消息为已读"""
        message_model = self.db.query(MessageModel).filter(
            MessageModel.id == message_id
        ).first()
        
        if not message_model:
            logger.warning(f"消息不存在: message_id={message_id}")
            return False
        
        message_model.is_read = True
        message_model.updated_at = datetime.now()
        self.db.commit()
        
        logger.info(f"消息已标记为已读: message_id={message_id}")
        return True
    
    async def mark_as_important(self, message_id: str, is_important: bool) -> bool:
        """标记消息为重点"""
        message_model = self.db.query(MessageModel).filter(
            MessageModel.id == message_id
        ).first()
        
        if not message_model:
            logger.warning(f"消息不存在: message_id={message_id}")
            return False
        
        message_model.is_important = is_important
        message_model.updated_at = datetime.now()
        self.db.commit()
        
        logger.info(f"消息重点状态已更新: message_id={message_id}, is_important={is_important}")
        return True
    
    async def get_recent_messages(self, conversation_id: str, limit: int = 10) -> List[Message]:
        """获取最近的消息"""
        message_models = self.db.query(MessageModel).options(
            joinedload(MessageModel.sender)
        ).filter(
            MessageModel.conversation_id == conversation_id
        ).order_by(
            MessageModel.timestamp.desc()
        ).limit(limit).all()
        
        # 按时间正序返回
        message_models.reverse()
        return [self._to_entity(msg) for msg in message_models]
    
    async def search_messages(self, conversation_id: str, query: str, skip: int = 0, limit: int = 50) -> List[Message]:
        """搜索消息"""
        message_models = self.db.query(MessageModel).options(
            joinedload(MessageModel.sender)
        ).filter(
            and_(
                MessageModel.conversation_id == conversation_id,
                MessageModel.content.contains(query)
            )
        ).order_by(
            MessageModel.timestamp.desc()
        ).offset(skip).limit(limit).all()
        
        return [self._to_entity(msg) for msg in message_models]
    
    async def delete_message(self, message_id: str, deleted_by: str) -> bool:
        """软删除消息"""
        message_model = self.db.query(MessageModel).filter(
            MessageModel.id == message_id
        ).first()
        
        if not message_model:
            logger.warning(f"消息不存在: message_id={message_id}")
            return False
        
        message_model.is_deleted = True
        message_model.deleted_at = datetime.now()
        message_model.deleted_by = deleted_by
        message_model.updated_at = datetime.now()
        
        self.db.commit()
        
        logger.info(f"消息已删除: message_id={message_id}")
        return True
