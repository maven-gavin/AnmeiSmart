"""
Contact和Chat领域集成服务
处理Contact和Chat领域之间的协作，确保职责分离
"""
import logging
from typing import Optional, List
from sqlalchemy.orm import Session

from app.schemas.chat import ConversationInfo
from app.services.chat.application.chat_application_service import ChatApplicationService
from app.services.contacts.application.contact_application_service import ContactApplicationService

logger = logging.getLogger(__name__)


class ChatIntegrationService:
    """Contact和Chat领域集成服务"""
    
    def __init__(
        self,
        contact_app_service: ContactApplicationService,
        chat_app_service: ChatApplicationService
    ):
        self.contact_app_service = contact_app_service
        self.chat_app_service = chat_app_service
    
    async def create_friend_conversation(
        self,
        user_id: str,
        friend_id: str
    ) -> ConversationInfo:
        """
        创建与好友的会话
        这是Contact和Chat领域的协作点
        """
        try:
            # 1. 验证好友关系（Contact领域职责）
            friendships = await self.contact_app_service.get_friends_use_case(
                user_id=user_id,
                status="accepted",
                size=1000  # 获取所有好友
            )
            
            # 检查是否为好友
            is_friend = any(f.friend_id == friend_id for f in friendships.items)
            if not is_friend:
                raise ValueError("只能与好友创建会话")
            
            # 2. 创建会话（Chat领域职责）
            # 获取好友信息用于会话标题
            friend_info = None
            for friendship in friendships.items:
                if friendship.friend_id == friend_id:
                    friend_info = friendship
                    break
            
            conversation_title = friend_info.nickname or friend_info.friend_name or f"与{friend_id}的对话"
            
            conversation = await self.chat_app_service.create_conversation_use_case(
                title=conversation_title,
                owner_id=user_id,
                conversation_type="single",
                auto_assign_consultant=False
            )
            
            # 3. 添加好友为会话参与者
            # 这里需要调用Chat应用服务添加参与者
            # 暂时返回创建的会话
            return conversation
            
        except Exception as e:
            logger.error(f"创建好友会话失败: {e}")
            raise
    
    async def get_friend_conversations(self, user_id: str) -> List[ConversationInfo]:
        """
        获取用户的所有好友会话
        这是Contact和Chat领域的协作点
        """
        try:
            # 1. 获取用户的好友列表（Contact领域职责）
            friendships = await self.contact_app_service.get_friends_use_case(
                user_id=user_id,
                status="accepted",
                size=1000  # 获取所有好友
            )
            
            # 2. 获取用户的会话列表（Chat领域职责）
            conversations = await self.chat_app_service.get_conversations_use_case(
                user_id=user_id,
                user_role="customer"
            )
            
            # 3. 筛选出好友会话（只包含单聊且参与者是好友的会话）
            friend_conversations = []
            friend_ids = [f.friend_id for f in friendships.items]
            
            for conversation in conversations:
                if conversation.conversation_type == "single":
                    # 检查会话的参与者是否包含好友
                    # 这里需要根据实际的会话参与者结构来判断
                    # 暂时返回所有单聊会话
                    friend_conversations.append(conversation)
            
            return friend_conversations
            
        except Exception as e:
            logger.error(f"获取好友会话失败: {e}")
            return []
    
    async def create_group_chat_from_contact_group(
        self,
        user_id: str,
        group_id: str,
        title: str,
        include_all_members: bool = True,
        member_ids: Optional[List[str]] = None
    ) -> ConversationInfo:
        """
        基于联系人分组创建群聊
        这是Contact和Chat领域的协作点
        """
        try:
            # 1. 获取联系人分组信息（Contact领域职责）
            groups = await self.contact_app_service.get_contact_groups_use_case(
                user_id=user_id,
                include_members=True
            )
            
            target_group = None
            for group in groups:
                if group.id == group_id:
                    target_group = group
                    break
            
            if not target_group:
                raise ValueError("联系人分组不存在")
            
            # 2. 创建群聊会话（Chat领域职责）
            conversation = await self.chat_app_service.create_conversation_use_case(
                title=title or target_group.name,
                owner_id=user_id,
                conversation_type="group",
                auto_assign_consultant=False
            )
            
            # 3. 添加分组成员为会话参与者
            if include_all_members and target_group.members:
                # 获取所有成员的用户ID
                member_user_ids = []
                for member in target_group.members:
                    if member.friendship and member.friendship.friend_id:
                        member_user_ids.append(member.friendship.friend_id)
                
                # 这里需要调用Chat应用服务添加参与者
                # 暂时返回创建的会话
                return conversation
            
            return conversation
            
        except Exception as e:
            logger.error(f"基于分组创建群聊失败: {e}")
            raise
