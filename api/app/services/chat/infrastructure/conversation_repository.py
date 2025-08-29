"""
会话仓储 - 基础设施层
负责数据持久化，外部服务集成，技术实现
遵循DDD分层架构的基础设施层职责
"""
from typing import List, Optional, Dict
from sqlalchemy.orm import Session, joinedload, subqueryload
from sqlalchemy import and_, or_
import logging
from datetime import datetime

from app.db.models.chat import Conversation as ConversationModel, Message as MessageModel, ConversationParticipant
from app.services.chat.domain.interfaces import IConversationRepository
from app.services.chat.domain.entities.conversation import Conversation
from app.services.chat.domain.entities.message import Message

logger = logging.getLogger(__name__)


class ConversationRepository(IConversationRepository):
    """会话仓储实现 - 基础设施层"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _to_entity(self, model: ConversationModel) -> Conversation:
        """ORM模型转领域实体"""
        return Conversation(
            id=str(model.id),
            title=model.title,
            owner_id=str(model.owner_id),
            conversation_type=model.type,
            is_active=model.is_active,
            is_archived=model.is_archived,
            message_count=model.message_count,
            unread_count=model.unread_count,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _to_model(self, entity: Conversation) -> ConversationModel:
        """领域实体转ORM模型"""
        return ConversationModel(
            id=entity.id,
            title=entity.title,
            type=entity.conversation_type,
            owner_id=entity.owner_id,
            is_active=entity.is_active,
            is_archived=entity.is_archived,
            message_count=entity.message_count,
            unread_count=entity.unread_count,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
    
    async def save(self, conversation: Conversation) -> Conversation:
        """保存会话"""
        conversation_model = self._to_model(conversation)
        self.db.add(conversation_model)
        self.db.commit()
        self.db.refresh(conversation_model)
        
        # 更新实体的时间戳
        conversation._updated_at = conversation_model.updated_at
        
        logger.info(f"会话保存成功: id={conversation.id}")
        return conversation
    
    async def get_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """根据ID获取会话"""
        conversation_model = self.db.query(ConversationModel).options(
            joinedload(ConversationModel.owner),
            joinedload(ConversationModel.first_participant)
        ).filter(ConversationModel.id == conversation_id).first()
        
        if not conversation_model:
            return None
        
        return self._to_entity(conversation_model)
    
    async def get_user_conversations(
        self,
        user_id: str,
        user_role: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Conversation]:
        """获取用户参与的会话列表"""
        # 构建查询：获取用户参与的所有会话
        query = self.db.query(ConversationModel).options(
            joinedload(ConversationModel.owner),
            joinedload(ConversationModel.first_participant),
            subqueryload(ConversationModel.participants).joinedload(ConversationParticipant.user)
        ).filter(
            # 用户是会话所有者
            ConversationModel.owner_id == user_id
        ).union(
            # 或者用户是会话参与者
            self.db.query(ConversationModel).options(
                joinedload(ConversationModel.owner),
                joinedload(ConversationModel.first_participant),
                subqueryload(ConversationModel.participants).joinedload(ConversationParticipant.user)
            ).join(
                ConversationParticipant,
                ConversationModel.id == ConversationParticipant.conversation_id
            ).filter(
                ConversationParticipant.user_id == user_id,
                ConversationParticipant.is_active == True
            )
        )
        
        # 按更新时间倒序排列，置顶会话优先
        conversation_models = query.order_by(
            ConversationModel.is_pinned.desc(),
            ConversationModel.pinned_at.desc(),
            ConversationModel.updated_at.desc()
        ).offset(skip).limit(limit).all()
        
        return [self._to_entity(conv) for conv in conversation_models]
    
    async def exists_by_title_and_owner(self, title: str, owner_id: str) -> bool:
        """检查用户是否已有同名会话"""
        return self.db.query(ConversationModel).filter(
            and_(
                ConversationModel.title == title,
                ConversationModel.owner_id == owner_id,
                ConversationModel.is_active == True
            )
        ).first() is not None
    
    async def get_last_message(self, conversation_id: str) -> Optional[Message]:
        """获取会话的最后一条消息"""
        message_model = self.db.query(MessageModel).filter(
            MessageModel.conversation_id == conversation_id
        ).order_by(MessageModel.timestamp.desc()).first()
        
        if not message_model:
            return None
        
        # 转换为领域实体
        return Message(
            id=str(message_model.id),
            conversation_id=str(message_model.conversation_id),
            content=message_model.content,
            message_type=message_model.type,
            sender_id=str(message_model.sender_id) if message_model.sender_id else None,
            sender_digital_human_id=str(message_model.sender_digital_human_id) if message_model.sender_digital_human_id else None,
            sender_type=message_model.sender_type,
            is_important=message_model.is_important,
            reply_to_message_id=str(message_model.reply_to_message_id) if message_model.reply_to_message_id else None,
            reactions=message_model.reactions,
            extra_metadata=message_model.extra_metadata,
            requires_confirmation=message_model.requires_confirmation,
            created_at=message_model.created_at,
            updated_at=message_model.updated_at
        )
    
    async def get_last_messages(self, conversation_ids: List[str]) -> Dict[str, Message]:
        """批量获取会话的最后消息"""
        if not conversation_ids:
            return {}
        
        # 使用子查询获取每个会话的最后消息
        from sqlalchemy import func
        subquery = self.db.query(
            MessageModel.conversation_id,
            func.max(MessageModel.timestamp).label('max_timestamp')
        ).filter(
            MessageModel.conversation_id.in_(conversation_ids)
        ).group_by(MessageModel.conversation_id).subquery()
        
        message_models = self.db.query(MessageModel).join(
            subquery,
            and_(
                MessageModel.conversation_id == subquery.c.conversation_id,
                MessageModel.timestamp == subquery.c.max_timestamp
            )
        ).all()
        
        result = {}
        for msg_model in message_models:
            message = Message(
                id=str(msg_model.id),
                conversation_id=str(msg_model.conversation_id),
                content=msg_model.content,
                message_type=msg_model.type,
                sender_id=str(msg_model.sender_id) if msg_model.sender_id else None,
                sender_digital_human_id=str(msg_model.sender_digital_human_id) if msg_model.sender_digital_human_id else None,
                sender_type=msg_model.sender_type,
                is_important=msg_model.is_important,
                reply_to_message_id=str(msg_model.reply_to_message_id) if msg_model.reply_to_message_id else None,
                reactions=msg_model.reactions,
                extra_metadata=msg_model.extra_metadata,
                requires_confirmation=msg_model.requires_confirmation,
                created_at=msg_model.created_at,
                updated_at=msg_model.updated_at
            )
            result[str(msg_model.conversation_id)] = message
        
        return result
    
    async def get_unread_count(self, conversation_id: str, user_id: str) -> int:
        """获取用户在指定会话中的未读消息数"""
        # 获取用户在此会话中的最后阅读时间
        participant = self.db.query(ConversationParticipant).filter(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == user_id
        ).first()
        
        if not participant or not participant.last_read_at:
            # 如果没有阅读记录，返回所有消息数
            return self.db.query(MessageModel).filter(
                MessageModel.conversation_id == conversation_id
            ).count()
        
        # 计算最后阅读时间之后的消息数
        unread_count = self.db.query(MessageModel).filter(
            MessageModel.conversation_id == conversation_id,
            MessageModel.timestamp > participant.last_read_at,
            MessageModel.sender_id != user_id  # 排除自己发送的消息
        ).count()
        
        return unread_count
    
    async def get_unread_counts(self, conversation_ids: List[str], user_id: str) -> Dict[str, int]:
        """批量获取用户在多个会话中的未读消息数"""
        if not conversation_ids:
            return {}
        
        result = {}
        for conv_id in conversation_ids:
            result[conv_id] = await self.get_unread_count(conv_id, user_id)
        
        return result
    
    async def delete(self, conversation_id: str) -> bool:
        """删除会话"""
        conversation = await self.get_by_id(conversation_id)
        if not conversation:
            return False
        
        # 软删除：标记为已归档
        conversation.archive()
        conversation_model = self._to_model(conversation)
        self.db.merge(conversation_model)
        self.db.commit()
        
        return True
    
    async def update_message_count(self, conversation_id: str, count: int) -> None:
        """更新会话消息数"""
        conversation = await self.get_by_id(conversation_id)
        if conversation:
            conversation._message_count = count
            conversation._updated_at = datetime.now()
            conversation_model = self._to_model(conversation)
            self.db.merge(conversation_model)
            self.db.commit()
    
    async def update_last_message_at(self, conversation_id: str, timestamp: datetime) -> None:
        """更新会话最后消息时间"""
        conversation = await self.get_by_id(conversation_id)
        if conversation:
            conversation._last_message_at = timestamp
            conversation._updated_at = datetime.now()
            conversation_model = self._to_model(conversation)
            self.db.merge(conversation_model)
            self.db.commit()
