"""结构化（blocking）LLM 调用。"""

from __future__ import annotations

import logging
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy.orm import Session

from app.ai.models.agent_config import AgentConfig
from app.ai.runtime.capabilities import AgentCapabilities
from app.ai.runtime.llm_factory import LLMFactory

logger = logging.getLogger(__name__)


class StructuredLLMRunner:
    """用于意图路由、洞察提取等 blocking JSON 场景。"""

    def __init__(self, db: Session):
        self.db = db

    async def invoke_text(
        self,
        agent_config: AgentConfig,
        capabilities: AgentCapabilities,
        prompt: str,
    ) -> str:
        llm = LLMFactory.create_chat_model(agent_config, capabilities, streaming=False)
        messages = []
        if capabilities.system_prompt:
            messages.append(SystemMessage(content=capabilities.system_prompt))
        messages.append(HumanMessage(content=prompt))

        response = await llm.ainvoke(messages)
        content = response.content
        if isinstance(content, list):
            content = "".join(str(part) for part in content)
        return str(content or "")

    @staticmethod
    def load_config(db: Session, agent_config_id: str) -> Optional[AgentConfig]:
        return (
            db.query(AgentConfig)
            .filter(AgentConfig.id == agent_config_id, AgentConfig.enabled.is_(True))
            .first()
        )

    @staticmethod
    def load_config_by_app_name(db: Session, app_name: str) -> Optional[AgentConfig]:
        return (
            db.query(AgentConfig)
            .filter(AgentConfig.enabled.is_(True), AgentConfig.app_name == app_name)
            .order_by(AgentConfig.created_at.desc())
            .first()
        )
