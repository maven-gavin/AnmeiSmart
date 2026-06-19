"""Agent 会话与消息持久化服务。"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.ai.models.agent_conversation import AgentConversation
from app.ai.models.agent_message import AgentMessage, AgentMessageFeedback
from app.ai.schemas.agent_chat import AgentConversationResponse, AgentMessageResponse
from app.common.deps.uuid_utils import generate_uuid

logger = logging.getLogger(__name__)


class ConversationService:
    """Agent 会话 CRUD（PostgreSQL 本地存储）。"""

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_conversation(
        self,
        *,
        agent_config_id: str,
        user_id: str,
        conversation_id: Optional[str],
        title: Optional[str] = None,
    ) -> AgentConversation:
        if conversation_id:
            conv = (
                self.db.query(AgentConversation)
                .filter(
                    AgentConversation.id == conversation_id,
                    AgentConversation.agent_config_id == agent_config_id,
                    AgentConversation.user_id == user_id,
                )
                .first()
            )
            if conv:
                return conv
            raise ValueError(f"会话不存在: {conversation_id}")

        conv = AgentConversation(
            agent_config_id=agent_config_id,
            user_id=user_id,
            title=title or "新对话",
        )
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def list_conversations(
        self,
        *,
        agent_config_id: str,
        user_id: str,
        limit: int = 100,
    ) -> List[AgentConversationResponse]:
        rows = (
            self.db.query(AgentConversation)
            .filter(
                AgentConversation.agent_config_id == agent_config_id,
                AgentConversation.user_id == user_id,
            )
            .order_by(AgentConversation.updated_at.desc())
            .limit(limit)
            .all()
        )

        result: List[AgentConversationResponse] = []
        for conv in rows:
            stats = (
                self.db.query(
                    func.count(AgentMessage.id),
                    func.max(AgentMessage.content),
                )
                .filter(AgentMessage.conversation_id == conv.id)
                .first()
            )
            message_count = int(stats[0] or 0) if stats else 0
            last_message = stats[1] if stats and stats[1] else None

            result.append(
                AgentConversationResponse(
                    id=conv.id,
                    agent_config_id=agent_config_id,
                    title=conv.title,
                    created_at=self._iso(conv.created_at),
                    updated_at=self._iso(conv.updated_at),
                    message_count=message_count,
                    last_message=last_message,
                )
            )
        return result

    def create_conversation(
        self,
        *,
        agent_config_id: str,
        user_id: str,
        title: Optional[str] = None,
    ) -> AgentConversationResponse:
        conv = self.get_or_create_conversation(
            agent_config_id=agent_config_id,
            user_id=user_id,
            conversation_id=None,
            title=title,
        )
        return AgentConversationResponse(
            id=conv.id,
            agent_config_id=agent_config_id,
            title=conv.title,
            created_at=self._iso(conv.created_at),
            updated_at=self._iso(conv.updated_at),
            message_count=0,
            last_message=None,
        )

    def update_conversation_title(
        self,
        *,
        agent_config_id: str,
        user_id: str,
        conversation_id: str,
        title: str,
    ) -> AgentConversationResponse:
        conv = self.get_or_create_conversation(
            agent_config_id=agent_config_id,
            user_id=user_id,
            conversation_id=conversation_id,
        )
        conv.title = title
        self.db.commit()
        self.db.refresh(conv)
        return AgentConversationResponse(
            id=conv.id,
            agent_config_id=agent_config_id,
            title=conv.title,
            created_at=self._iso(conv.created_at),
            updated_at=self._iso(conv.updated_at),
            message_count=0,
            last_message=None,
        )

    def delete_conversation(
        self,
        *,
        agent_config_id: str,
        user_id: str,
        conversation_id: str,
    ) -> bool:
        conv = (
            self.db.query(AgentConversation)
            .filter(
                AgentConversation.id == conversation_id,
                AgentConversation.agent_config_id == agent_config_id,
                AgentConversation.user_id == user_id,
            )
            .first()
        )
        if not conv:
            raise ValueError(f"会话不存在: {conversation_id}")
        self.db.delete(conv)
        self.db.commit()
        return True

    def add_message(
        self,
        *,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        is_error: bool = False,
        message_id: Optional[str] = None,
    ) -> AgentMessage:
        msg = AgentMessage(
            id=message_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            is_error=is_error,
            extra_metadata=metadata,
        )
        self.db.add(msg)

        conv = self.db.query(AgentConversation).filter(AgentConversation.id == conversation_id).first()
        if conv:
            if role == "user" and conv.title == "新对话" and content.strip():
                conv.title = content.strip()[:50]
            conv.updated_at = datetime.now()

        self.db.commit()
        self.db.refresh(msg)
        return msg

    def list_messages(
        self,
        *,
        conversation_id: str,
        limit: int = 50,
    ) -> List[AgentMessageResponse]:
        rows = (
            self.db.query(AgentMessage)
            .filter(AgentMessage.conversation_id == conversation_id)
            .order_by(AgentMessage.created_at.asc())
            .limit(limit)
            .all()
        )
        result: List[AgentMessageResponse] = []
        for msg in rows:
            result.append(
                AgentMessageResponse(
                    id=msg.id,
                    conversation_id=conversation_id,
                    content=msg.content,
                    is_answer=msg.role == "assistant",
                    timestamp=self._iso(msg.created_at),
                    agent_thoughts=(msg.extra_metadata or {}).get("agent_thoughts"),
                    files=(msg.extra_metadata or {}).get("files"),
                    is_error=msg.is_error,
                )
            )
        return result

    def get_recent_langchain_history(self, conversation_id: str, limit: int = 20) -> List[AgentMessage]:
        rows = (
            self.db.query(AgentMessage)
            .filter(AgentMessage.conversation_id == conversation_id)
            .order_by(AgentMessage.created_at.desc())
            .limit(limit)
            .all()
        )
        rows.reverse()
        return rows

    def save_feedback(self, *, message_id: str, user_id: str, rating: str) -> Dict[str, Any]:
        existing = (
            self.db.query(AgentMessageFeedback)
            .filter(
                AgentMessageFeedback.message_id == message_id,
                AgentMessageFeedback.user_id == user_id,
            )
            .first()
        )
        if existing:
            existing.rating = rating
        else:
            self.db.add(
                AgentMessageFeedback(
                    id=generate_uuid(),
                    message_id=message_id,
                    user_id=user_id,
                    rating=rating,
                )
            )
        self.db.commit()
        return {"result": "success"}

    @staticmethod
    def _iso(dt: Optional[datetime]) -> str:
        if not dt:
            return datetime.now().isoformat()
        return dt.isoformat()
