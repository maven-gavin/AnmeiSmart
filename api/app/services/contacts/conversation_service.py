"""
通讯录会话服务 - 处理好友间的会话创建和管理
"""
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from datetime import datetime
import logging

from app.db.models.chat import Conversation, ConversationParticipant
from app.db.models.user import User
from app.db.models.contacts import Friendship
from app.db.uuid_utils import conversation_id, message_id
from app.schemas.chat import ConversationInfo

logger = logging.getLogger(__name__)


class ContactConversationService:
    """通讯录会话服务 - 专门处理好友间的会话管理"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_or_create_friend_conversation(
        self, 
        user_id: str, 
        friend_id: str
    ) -> ConversationInfo:
        """
        获取或创建与好友的单聊会话
        确保两个用户之间只有一个活跃的单聊会话
        """
        try:
            # 1. 验证好友关系
            friendship = await self._verify_friendship(user_id, friend_id)
            if not friendship:
                raise ValueError("用户间不存在好友关系")
            
            # 2. 查找现有的单聊会话
            existing_conversation = await self._find_existing_friend_conversation(user_id, friend_id)
            if existing_conversation:
                logger.info(f"找到现有好友会话: {existing_conversation.id}")
                return self._convert_to_conversation_info(existing_conversation)
            
            # 3. 创建新的单聊会话
            new_conversation = await self._create_friend_conversation(user_id, friend_id)
            logger.info(f"创建新好友会话: {new_conversation.id}")
            return self._convert_to_conversation_info(new_conversation)
            
        except Exception as e:
            logger.error(f"获取或创建好友会话失败: {e}")
            raise
    
    async def _verify_friendship(self, user_id: str, friend_id: str) -> Optional[Friendship]:
        """验证用户间的好友关系"""
        friendship = self.db.query(Friendship).filter(
            Friendship.user_id == user_id,
            Friendship.friend_id == friend_id,
            Friendship.status == "accepted"
        ).first()
        
        return friendship
    
    async def _find_existing_friend_conversation(
        self, 
        user_id: str, 
        friend_id: str
    ) -> Optional[Conversation]:
        """
        查找两个用户之间现有的单聊会话
        使用优化的查询逻辑，通过first_participant_id字段提升查询效率
        """
        try:
            # 优化查询：使用first_participant_id字段快速定位好友会话
            # 查询条件：单聊 + 非咨询会话 + 活跃状态 + 参与者匹配
            
            # 方案1：user_id是所有者，friend_id是第一个参与者
            conversation1 = self.db.query(Conversation).filter(
                Conversation.chat_mode == "single",
                Conversation.tag == "chat",
                Conversation.is_active == True,
                Conversation.owner_id == user_id,
                Conversation.first_participant_id == friend_id
            ).first()
            
            if conversation1:
                logger.info(f"找到现有好友会话(方案1): {conversation1.id}")
                return conversation1
            
            # 方案2：friend_id是所有者，user_id是第一个参与者
            conversation2 = self.db.query(Conversation).filter(
                Conversation.chat_mode == "single",
                Conversation.tag == "chat",
                Conversation.is_active == True,
                Conversation.owner_id == friend_id,
                Conversation.first_participant_id == user_id
            ).first()
            
            if conversation2:
                logger.info(f"找到现有好友会话(方案2): {conversation2.id}")
                return conversation2
            
            # 如果优化查询没找到，回退到原有的参与者查询逻辑（兼容旧数据）
            return await self._find_conversation_by_participants(user_id, friend_id)
            
        except Exception as e:
            logger.error(f"查找现有好友会话失败: {e}")
            return None
    
    async def _find_conversation_by_participants(
        self, 
        user_id: str, 
        friend_id: str
    ) -> Optional[Conversation]:
        """
        通过参与者查询会话（兼容旧数据的回退方案）
        """
        try:
            # 查询同时包含两个用户的单聊会话
            common_conversations = self.db.query(Conversation).join(
                ConversationParticipant, Conversation.id == ConversationParticipant.conversation_id
            ).filter(
                Conversation.chat_mode == "single",
                Conversation.tag == "chat",
                Conversation.is_active == True,
                ConversationParticipant.user_id.in_([user_id, friend_id]),
                ConversationParticipant.is_active == True
            ).options(
                joinedload(Conversation.participants)
            ).all()
            
            # 验证找到的会话确实只包含这两个用户
            for conversation in common_conversations:
                active_participants = [
                    p for p in conversation.participants 
                    if p.is_active and p.user_id is not None
                ]
                
                if len(active_participants) == 2:
                    participant_ids = {p.user_id for p in active_participants}
                    if participant_ids == {user_id, friend_id}:
                        logger.info(f"通过参与者查询找到好友会话: {conversation.id}")
                        return conversation
            
            return None
            
        except Exception as e:
            logger.error(f"通过参与者查询好友会话失败: {e}")
            return None
    
    async def _create_friend_conversation(
        self, 
        user_id: str, 
        friend_id: str
    ) -> Conversation:
        """创建新的好友单聊会话"""
        try:
            # 获取用户信息
            user = self.db.query(User).filter(User.id == user_id).first()
            friend = self.db.query(User).filter(User.id == friend_id).first()
            
            if not user or not friend:
                raise ValueError("用户不存在")
            
            # 创建会话标题
            title = f"{user.username} 与 {friend.username} 的对话"
            
            # 创建会话
            new_conversation = Conversation(
                id=conversation_id(),
                title=title,
                chat_mode="single",
                tag="chat",  # 好友聊天标签为chat
                owner_id=user_id,  # 发起者为所有者
                first_participant_id=friend_id,  # 好友为第一个参与者
                is_pinned=False,
                is_active=True,
                is_archived=False,
                message_count=0,
                unread_count=0
            )
            
            self.db.add(new_conversation)
            self.db.flush()  # 获取ID
            
            # 创建参与者记录
            # 参与者1：发起者（所有者）
            participant1 = ConversationParticipant(
                id=message_id(),
                conversation_id=new_conversation.id,
                user_id=user_id,
                role="owner",
                takeover_status="no_takeover",
                is_active=True,
                joined_at=datetime.now()
            )
            self.db.add(participant1)
            
            # 参与者2：好友
            participant2 = ConversationParticipant(
                id=message_id(),
                conversation_id=new_conversation.id,
                user_id=friend_id,
                role="member",
                takeover_status="no_takeover",
                is_active=True,
                joined_at=datetime.now()
            )
            self.db.add(participant2)
            
            self.db.commit()
            
            logger.info(f"创建好友会话成功: {new_conversation.id}, 参与者: {user_id}, {friend_id}")
            return new_conversation
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建好友会话失败: {e}")
            raise
    
    def _convert_to_conversation_info(self, conversation: Conversation) -> ConversationInfo:
        """将Conversation模型转换为ConversationInfo"""
        return ConversationInfo(
            id=conversation.id,
            title=conversation.title,
            type=conversation.type,
            owner_id=conversation.owner_id,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            is_active=conversation.is_active,
            is_archived=conversation.is_archived,
            message_count=conversation.message_count,
            unread_count=conversation.unread_count,
            last_message_at=conversation.last_message_at
        )
    
    async def get_friend_conversations(self, user_id: str) -> List[ConversationInfo]:
        """获取用户的所有好友会话"""
        try:
            # 查询用户参与的所有单聊会话
            conversations = self.db.query(Conversation).join(ConversationParticipant).filter(
                ConversationParticipant.user_id == user_id,
                ConversationParticipant.is_active == True,
                Conversation.type == "single",
                Conversation.is_active == True
            ).options(
                joinedload(Conversation.participants)
            ).order_by(Conversation.last_message_at.desc()).all()
            
            result = []
            for conversation in conversations:
                # 获取对话的另一个参与者（好友）
                other_participant = None
                for participant in conversation.participants:
                    if participant.user_id != user_id and participant.is_active:
                        other_participant = participant
                        break
                
                if other_participant:
                    # 验证是否为好友关系
                    friendship = await self._verify_friendship(user_id, other_participant.user_id)
                    if friendship:
                        conv_info = self._convert_to_conversation_info(conversation)
                        result.append(conv_info)
            
            return result
            
        except Exception as e:
            logger.error(f"获取好友会话列表失败: {e}")
            return []
    
    async def update_conversation_activity(
        self, 
        conversation_id: str, 
        user_id: str, 
        friend_id: str
    ):
        """更新会话活跃状态和好友互动记录"""
        try:
            # 更新会话最后消息时间
            conversation = self.db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            
            if conversation:
                conversation.last_message_at = datetime.now()
                conversation.updated_at = datetime.now()
            
            # 更新好友互动记录
            friendship = self.db.query(Friendship).filter(
                Friendship.user_id == user_id,
                Friendship.friend_id == friend_id
            ).first()
            
            if friendship:
                friendship.last_interaction_at = datetime.now()
                friendship.interaction_count += 1
            
            # 更新反向好友关系
            reverse_friendship = self.db.query(Friendship).filter(
                Friendship.user_id == friend_id,
                Friendship.friend_id == user_id
            ).first()
            
            if reverse_friendship:
                reverse_friendship.last_interaction_at = datetime.now()
                reverse_friendship.interaction_count += 1
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"更新会话活跃状态失败: {e}")
            self.db.rollback()
