"""
Agent 对话服务
负责协调 LangGraph Agent 对话的完整流程
"""

import logging
from typing import Optional, Dict, Any, List, AsyncIterator

from sqlalchemy.orm import Session

from app.ai.schemas.agent_chat import AgentMessageResponse, AgentConversationResponse
from app.ai.services.agent_runtime_service import AgentRuntimeService
from app.ai.services.conversation_service import ConversationService
from app.chat.services.chat_service import ChatService
from app.websocket.broadcasting_service import BroadcastingService

logger = logging.getLogger(__name__)


class AgentChatService:
    """Agent 对话服务（LangGraph 运行时）。"""

    def __init__(
        self,
        runtime: AgentRuntimeService,
        conversation_service: ConversationService,
        chat_service: ChatService,
        broadcasting_service: Optional[BroadcastingService],
        db: Session,
    ):
        self.runtime = runtime
        self.conversations = conversation_service
        self.chat_service = chat_service
        self.broadcasting_service = broadcasting_service
        self.db = db

    async def stream_chat(
        self,
        agent_config_id: str,
        user_id: str,
        message: str,
        conversation_id: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[bytes]:
        async for chunk in self.runtime.stream_chat(
            agent_config_id=agent_config_id,
            user_id=user_id,
            message=message,
            conversation_id=conversation_id,
            inputs=inputs,
        ):
            yield chunk

    async def get_conversations(
        self,
        agent_config_id: str,
        user_id: str,
    ) -> List[AgentConversationResponse]:
        return self.conversations.list_conversations(
            agent_config_id=agent_config_id,
            user_id=user_id,
        )

    async def create_conversation(
        self,
        agent_config_id: str,
        user_id: str,
        title: Optional[str] = None,
    ) -> AgentConversationResponse:
        return self.conversations.create_conversation(
            agent_config_id=agent_config_id,
            user_id=user_id,
            title=title,
        )

    async def get_messages(
        self,
        agent_config_id: str,
        conversation_id: str,
        user_id: str,
        limit: int = 50,
    ) -> List[AgentMessageResponse]:
        self.runtime._load_agent_config(agent_config_id)
        self.conversations.get_or_create_conversation(
            agent_config_id=agent_config_id,
            user_id=user_id,
            conversation_id=conversation_id,
        )
        return self.conversations.list_messages(conversation_id=conversation_id, limit=limit)

    async def delete_conversation(
        self,
        agent_config_id: str,
        conversation_id: str,
        user_id: str,
    ) -> bool:
        return self.conversations.delete_conversation(
            agent_config_id=agent_config_id,
            user_id=user_id,
            conversation_id=conversation_id,
        )

    async def update_conversation(
        self,
        agent_config_id: str,
        conversation_id: str,
        user_id: str,
        title: str,
    ) -> AgentConversationResponse:
        return self.conversations.update_conversation_title(
            agent_config_id=agent_config_id,
            user_id=user_id,
            conversation_id=conversation_id,
            title=title,
        )

    async def message_feedback(
        self,
        agent_config_id: str,
        message_id: str,
        rating: str,
        user_id: str,
    ) -> Dict[str, Any]:
        self.runtime._load_agent_config(agent_config_id)
        return self.runtime.message_feedback(message_id=message_id, user_id=user_id, rating=rating)

    async def get_suggested_questions(
        self,
        agent_config_id: str,
        message_id: str,
        user_id: str,
    ) -> List[str]:
        return await self.runtime.get_suggested_questions(
            agent_config_id=agent_config_id,
            message_id=message_id,
            user_id=user_id,
        )

    async def stop_message_generation(
        self,
        agent_config_id: str,
        task_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        self.runtime._load_agent_config(agent_config_id)
        return self.runtime.stop_message_generation(task_id)

    async def audio_to_text(
        self,
        agent_config_id: str,
        audio_file: Any,
        user_id: str,
    ) -> str:
        return await self.runtime.audio_to_text(agent_config_id, audio_file, user_id)

    async def text_to_audio(
        self,
        agent_config_id: str,
        text: str,
        user_id: str,
        streaming: bool = False,
    ) -> Dict[str, Any]:
        return await self.runtime.text_to_audio(agent_config_id, text, user_id, streaming)

    async def upload_file(
        self,
        agent_config_id: str,
        file: Any,
        user_id: str,
    ) -> Dict[str, Any]:
        return await self.runtime.upload_file(agent_config_id, file, user_id)

    async def get_application_parameters(
        self,
        agent_config_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        return await self.runtime.get_application_parameters(agent_config_id)

    async def get_application_meta(
        self,
        agent_config_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        return self.runtime.get_application_meta(agent_config_id)
