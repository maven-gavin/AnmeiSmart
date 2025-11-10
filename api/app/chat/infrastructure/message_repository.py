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
from app.chat.domain.entities.message import MessageEntity

logger = logging.getLogger(__name__)


class MessageRepository(IMessageRepository):
    """消息仓储实现 - 基础设施层"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _to_entity(self, model: MessageModel) -> MessageEntity:
        """ORM模型转领域实体"""
        return MessageEntity(
            id=str(model.id),
            conversationId=str(model.conversation_id),
            content=model.content,
            messageType=model.type,
            senderId=str(model.sender_id) if model.sender_id else None,
            senderDigitalHumanId=str(model.sender_digital_human_id) if model.sender_digital_human_id else None,
            senderType=model.sender_type,
            isImportant=model.is_important,
            replyToMessageId=str(model.reply_to_message_id) if model.reply_to_message_id else None,
            reactions=model.reactions,
            extraMetadata=model.extra_metadata,
            requiresConfirmation=model.requires_confirmation,
            createdAt=model.created_at,
            updatedAt=model.updated_at,
            isRead=model.is_read,
            isDeleted=model.is_deleted,
            deletedAt=model.deleted_at,
            deletedBy=model.deleted_by
        )
    
    def _to_model(self, entity: MessageEntity) -> MessageModel:
        """领域实体转ORM模型"""
        return MessageModel(
            id=entity.id,
            conversation_id=entity.conversationId,
            content=entity.content,
            type=entity.messageType,
            sender_id=entity.senderId,
            sender_digital_human_id=entity.senderDigitalHumanId,
            sender_type=entity.senderType,
            is_important=entity.isImportant,
            reply_to_message_id=entity.replyToMessageId,
            reactions=entity.reactions,
            extra_metadata=entity.extraMetadata,
            requires_confirmation=entity.requiresConfirmation,
            created_at=entity.createdAt,
            updated_at=entity.updatedAt,
            is_read=entity.isRead,
            is_deleted=entity.isDeleted,
            deleted_at=entity.deletedAt,
            deleted_by=entity.deletedBy
        )
    
    async def save(self, message: MessageEntity) -> MessageEntity:
        """保存消息"""
        message_model = self._to_model(message)
        self.db.add(message_model)
        self.db.commit()
        self.db.refresh(message_model)
        
        # 更新实体的时间戳
        message.updated_at = message_model.updated_at
        
        logger.info(f"消息保存成功: id={message.id}")
        return message
    
    async def get_by_id(self, message_id: str) -> Optional[MessageEntity]:
        """根据ID获取消息"""
        message_model = self.db.query(MessageModel).options(
            joinedload(MessageModel.sender)
        ).filter(MessageModel.id == message_id).first()
        
        if not message_model:
            return None
        
        return self._to_entity(message_model)
    
    async def get_conversation_messages(self, conversation_id: str, skip: int = 0, limit: int = 100) -> List[MessageEntity]:
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
    
    async def get_conversation_messages_with_senders(self, conversation_id: str, skip: int = 0, limit: int = 100) -> tuple[List[MessageEntity], dict, dict]:
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
    
    async def get_recent_messages(self, conversation_id: str, limit: int = 10) -> List[MessageEntity]:
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
    
    async def search_messages(self, conversation_id: str, query: str, skip: int = 0, limit: int = 50) -> List[MessageEntity]:
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
