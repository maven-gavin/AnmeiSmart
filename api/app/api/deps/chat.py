"""
聊天相关依赖模块 - 聊天服务、消息处理等
"""
import logging
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import Depends

from app.db.base import get_db
from app.services.chat.application import ChatApplicationService
from app.services.chat.domain import ConversationDomainService, MessageDomainService
from app.services.chat.infrastructure.message_repository import MessageRepository
from app.services.chat.infrastructure.conversation_repository import ConversationRepository
from app.services.websocket.broadcasting_factory import get_broadcasting_service

logger = logging.getLogger(__name__)


def get_message_repository(db: Session = Depends(get_db)) -> MessageRepository:
    """获取消息仓储实例"""
    return MessageRepository(db)


def get_conversation_repository(db: Session = Depends(get_db)) -> ConversationRepository:
    """获取会话仓储实例"""
    return ConversationRepository(db)


def get_conversation_domain_service(
    conversation_repository: ConversationRepository = Depends(get_conversation_repository)
) -> ConversationDomainService:
    """获取会话领域服务实例"""
    return ConversationDomainService(conversation_repository)


def get_message_domain_service(
    message_repository: MessageRepository = Depends(get_message_repository)
) -> MessageDomainService:
    """获取消息领域服务实例"""
    return MessageDomainService(message_repository)


async def get_chat_application_service(
    conversation_repository: ConversationRepository = Depends(get_conversation_repository),
    message_repository: MessageRepository = Depends(get_message_repository),
    conversation_domain_service: ConversationDomainService = Depends(get_conversation_domain_service),
    message_domain_service: MessageDomainService = Depends(get_message_domain_service),
    db: Session = Depends(get_db)
) -> ChatApplicationService:
    """获取聊天应用服务实例"""
    try:
        broadcasting_service = await get_broadcasting_service(db)
        return ChatApplicationService(
            conversation_repository=conversation_repository,
            message_repository=message_repository,
            conversation_domain_service=conversation_domain_service,
            message_domain_service=message_domain_service,
            broadcasting_service=broadcasting_service
        )
    except Exception as e:
        logger.warning(f"创建广播服务失败，使用基础ChatApplicationService: {e}")
        return ChatApplicationService(
            conversation_repository=conversation_repository,
            message_repository=message_repository,
            conversation_domain_service=conversation_domain_service,
            message_domain_service=message_domain_service
        )

__all__ = [
    "get_message_repository",
    "get_conversation_repository", 
    "get_conversation_domain_service",
    "get_message_domain_service",
    "get_chat_application_service"
]
