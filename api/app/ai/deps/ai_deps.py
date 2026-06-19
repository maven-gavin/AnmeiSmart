"""
AI模块依赖注入配置
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.deps import get_db
from app.ai.services.agent_config_service import AgentConfigService
from app.ai.services.agent_runtime_service import AgentRuntimeService
from app.ai.services.conversation_service import ConversationService
from app.chat.services.chat_service import ChatService
from app.chat.deps.chat import get_chat_service
from app.websocket.broadcasting_service import BroadcastingService
from app.websocket.broadcasting_factory import get_broadcasting_service_dependency


def get_agent_config_service(db: Session = Depends(get_db)) -> AgentConfigService:
    return AgentConfigService(db)


def get_agent_runtime_service(db: Session = Depends(get_db)) -> AgentRuntimeService:
    return AgentRuntimeService(db)


def get_agent_chat_service(
    db: Session = Depends(get_db),
    chat_service: ChatService = Depends(get_chat_service),
    broadcasting_service: BroadcastingService = Depends(get_broadcasting_service_dependency),
):
    from app.ai.services.agent_chat_service import AgentChatService

    runtime = AgentRuntimeService(db)
    conversation_service = ConversationService(db)
    return AgentChatService(
        runtime=runtime,
        conversation_service=conversation_service,
        chat_service=chat_service,
        broadcasting_service=broadcasting_service,
        db=db,
    )
