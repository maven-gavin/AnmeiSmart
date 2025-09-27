"""
聊天相关依赖模块 - 聊天服务、消息处理等
"""
import logging
from sqlalchemy.orm import Session
from fastapi import Depends

from app.common.infrastructure.db.base import get_db
from app.chat.application.chat_application_service import ChatApplicationService
from app.chat.domain.conversation_domain_service import ConversationDomainService
from app.chat.domain.message_domain_service import MessageDomainService
from app.chat.infrastructure.message_repository import MessageRepository
from app.chat.infrastructure.conversation_repository import ConversationRepository
from app.websocket.broadcasting_factory import get_broadcasting_service

logger = logging.getLogger(__name__)


def get_message_repository(db: Session = Depends(get_db)) -> MessageRepository:
    """获取消息仓储实例"""
    return MessageRepository(db)


def get_conversation_repository(db: Session = Depends(get_db)) -> ConversationRepository:
    """获取会话仓储实例"""
    logger.info(f"依赖注入：创建ConversationRepository，db类型: {type(db)}")
    repo = ConversationRepository(db)
    logger.info(f"依赖注入：ConversationRepository创建成功，类型: {type(repo)}")
    return repo


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
    logger.info("依赖注入：开始创建ChatApplicationService")
    logger.info(f"conversation_repository类型: {type(conversation_repository)}")
    logger.info(f"message_repository类型: {type(message_repository)}")
    
    try:
        logger.info("依赖注入：尝试获取广播服务")
        broadcasting_service = await get_broadcasting_service(db)
        logger.info(f"依赖注入：广播服务创建成功，类型: {type(broadcasting_service)}")
        
        service = ChatApplicationService(
            conversation_repository=conversation_repository,
            message_repository=message_repository,
            conversation_domain_service=conversation_domain_service,
            message_domain_service=message_domain_service,
            broadcasting_service=broadcasting_service
        )
        logger.info("依赖注入：ChatApplicationService创建成功（含广播服务）")
        return service
        
    except Exception as e:
        logger.warning(f"创建广播服务失败，使用基础ChatApplicationService: {e}")
        service = ChatApplicationService(
            conversation_repository=conversation_repository,
            message_repository=message_repository,
            conversation_domain_service=conversation_domain_service,
            message_domain_service=message_domain_service
        )
        logger.info("依赖注入：ChatApplicationService创建成功（无广播服务）")
        return service

__all__ = [
    "get_message_repository",
    "get_conversation_repository", 
    "get_conversation_domain_service",
    "get_message_domain_service",
    "get_chat_application_service"
]
