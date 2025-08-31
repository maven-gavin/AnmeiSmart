"""
咨询会话应用服务
负责咨询会话相关的用例编排和事务管理
遵循DDD分层架构，集成ChatApplicationService处理会话管理
"""
from typing import Optional, List, Dict, Any
import logging

from app.schemas.chat import ConversationInfo
from app.services.chat.application.chat_application_service import ChatApplicationService

logger = logging.getLogger(__name__)


class ConsultationSessionApplicationService:
    """咨询会话应用服务 - 编排咨询会话相关的用例"""
    
    def __init__(self, chat_application_service: ChatApplicationService):
        self.chat_application_service = chat_application_service
    
    async def create_consultation_session_use_case(self, user_id: str) -> ConversationInfo:
        """创建咨询会话用例"""
        try:
            logger.info(f"创建咨询会话: user_id={user_id}")
            
            # 调用ChatApplicationService创建咨询会话
            conversation = await self.chat_application_service.create_conversation_use_case(
                title="咨询会话",
                owner_id=user_id,
                chat_mode="consultation",
                auto_assign_consultant=True
            )
            
            return conversation
            
        except Exception as e:
            logger.error(f"创建咨询会话失败: {e}")
            raise
    
    async def create_first_message_task_use_case(self, conversation_id: str, user_id: str) -> str:
        """创建第一条消息任务用例"""
        try:
            logger.info(f"创建第一条消息任务: conversation_id={conversation_id}, user_id={user_id}")
            
            # 这里应该创建待办任务，通知顾问有新的咨询
            # 暂时返回一个模拟的任务ID
            task_id = f"consultation_task_{conversation_id}_{user_id}"
            
            # TODO: 集成任务管理系统
            # task_service.create_consultation_task(conversation_id, user_id)
            
            return task_id
            
        except Exception as e:
            logger.error(f"创建第一条消息任务失败: {e}")
            raise
    
    async def assign_consultant_use_case(self, conversation_id: str, consultant_id: str, task_id: str) -> bool:
        """分配顾问用例"""
        try:
            logger.info(f"分配顾问: conversation_id={conversation_id}, consultant_id={consultant_id}, task_id={task_id}")
            
            # 这里应该更新会话的顾问分配
            # 暂时返回成功
            # TODO: 集成会话管理，更新会话的assigned_consultant_id
            
            return True
            
        except Exception as e:
            logger.error(f"分配顾问失败: {e}")
            raise
    
    async def pin_conversation_use_case(self, conversation_id: str, user_id: str, pin: bool) -> bool:
        """置顶会话用例"""
        try:
            logger.info(f"置顶会话: conversation_id={conversation_id}, user_id={user_id}, pin={pin}")
            
            # 调用ChatApplicationService更新会话
            updates = {"is_pinned": pin}
            await self.chat_application_service.update_conversation(
                conversation_id=conversation_id,
                user_id=user_id,
                updates=updates
            )
            
            return True
            
        except Exception as e:
            logger.error(f"置顶会话失败: {e}")
            raise
    
    async def get_conversations_use_case(
        self,
        user_id: str,
        include_consultation: bool = True,
        include_friend_chat: bool = True
    ) -> List[ConversationInfo]:
        """获取会话列表用例"""
        try:
            logger.info(f"获取会话列表: user_id={user_id}")
            
            # 获取用户角色
            user_role = "customer"  # 这里应该从用户服务获取实际角色
            
            # 调用ChatApplicationService获取会话列表
            conversations = await self.chat_application_service.get_conversations_use_case(
                user_id=user_id,
                user_role=user_role,
                skip=0,
                limit=100
            )
            
            # 根据参数过滤会话类型
            filtered_conversations = []
            for conv in conversations:
                if include_consultation and conv.chat_mode == "consultation":
                    filtered_conversations.append(conv)
                elif include_friend_chat and conv.chat_mode == "single":
                    filtered_conversations.append(conv)
            
            return filtered_conversations
            
        except Exception as e:
            logger.error(f"获取会话列表失败: {e}")
            raise
