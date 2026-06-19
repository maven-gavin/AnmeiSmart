"""LangGraph Agent 流式运行时。"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator, Dict, List, Optional

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from sqlalchemy.orm import Session

from app.ai.models.agent_config import AgentConfig
from app.ai.models.agent_knowledge_base import AgentKnowledgeBase
from app.ai.models.agent_message import AgentMessage
from app.ai.rag.retriever_tool import build_rag_tool
from app.ai.runtime.input_resolver import InputContextResolver
from app.ai.runtime.mcp_tools import build_mcp_tools_for_groups
from app.ai.runtime.capabilities import AgentCapabilities
from app.ai.runtime.llm_factory import LLMFactory
from app.ai.runtime.sse_emitter import (
    emit_agent_thought,
    emit_error,
    emit_message_chunk,
    emit_message_end,
    new_task_id,
)
from app.ai.runtime.task_registry import AgentTaskRegistry
from app.ai.utils.stream_buffer import StreamBuffer

logger = logging.getLogger(__name__)


class AgentRunner:
    """基于 langchain create_agent + langgraph 的流式 Agent 执行器。"""

    def __init__(self, db: Session):
        self.db = db
        self.input_resolver = InputContextResolver(db)

    def _build_tools(self, agent_config: AgentConfig, capabilities: AgentCapabilities) -> list:
        tools: list = []
        if capabilities.enable_tools and capabilities.mcp_tool_groups:
            tools.extend(build_mcp_tools_for_groups(self.db, capabilities.mcp_tool_groups))
        if capabilities.enable_rag and capabilities.knowledge_base_id:
            kb = (
                self.db.query(AgentKnowledgeBase)
                .filter(
                    AgentKnowledgeBase.id == capabilities.knowledge_base_id,
                    AgentKnowledgeBase.enabled.is_(True),
                )
                .first()
            )
            if kb:
                tools.append(build_rag_tool(self.db, agent_config, kb))
        return tools

    def _build_langchain_messages(
        self,
        history: List[AgentMessage],
        query: str,
        inputs: Optional[Dict[str, Any]],
    ) -> list:
        messages: list = []
        for item in history:
            if item.role == "user":
                messages.append(HumanMessage(content=item.content))
            elif item.role == "assistant":
                messages.append(AIMessage(content=item.content))

        user_text = self.input_resolver.enrich_user_message(query, inputs)
        messages.append(HumanMessage(content=user_text))
        return messages

    async def stream_chat(
        self,
        *,
        agent_config: AgentConfig,
        capabilities: AgentCapabilities,
        history: List[AgentMessage],
        query: str,
        conversation_id: str,
        message_id: str,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[bytes]:
        task_id = new_task_id()
        cancel_event = AgentTaskRegistry.register(task_id)
        stream_buffer = StreamBuffer()
        full_answer = ""

        try:
            llm = LLMFactory.create_chat_model(agent_config, capabilities, streaming=True)
            tools = self._build_tools(agent_config, capabilities) if capabilities.enable_tools else []
            agent = create_agent(
                model=llm,
                tools=tools,
                system_prompt=capabilities.system_prompt or "You are a helpful assistant.",
            )

            lc_messages = self._build_langchain_messages(history, query, inputs)
            input_state = {"messages": lc_messages}

            async for item in agent.astream(input_state, stream_mode=["messages"]):
                if cancel_event.is_set():
                    break

                msg_chunk = self._extract_message_chunk(item)
                if msg_chunk is None or not hasattr(msg_chunk, "content"):
                    continue

                text_part = msg_chunk.content
                if not text_part:
                    continue
                if isinstance(text_part, list):
                    text_part = "".join(
                        p.get("text", "") if isinstance(p, dict) else str(p) for p in text_part
                    )
                if not text_part:
                    continue

                full_answer += text_part
                normal, think = stream_buffer.process(text_part)
                if normal:
                    yield emit_message_chunk(
                        answer=normal,
                        conversation_id=conversation_id,
                        message_id=message_id,
                        task_id=task_id,
                    )
                if think:
                    yield emit_agent_thought(
                        thought=think,
                        conversation_id=conversation_id,
                        message_id=message_id,
                        task_id=task_id,
                    )

            normal_remaining, think_remaining = stream_buffer.flush()
            if normal_remaining:
                yield emit_message_chunk(
                    answer=normal_remaining,
                    conversation_id=conversation_id,
                    message_id=message_id,
                    task_id=task_id,
                )
            if think_remaining:
                yield emit_agent_thought(
                    thought=think_remaining,
                    conversation_id=conversation_id,
                    message_id=message_id,
                    task_id=task_id,
                )

            yield emit_message_end(
                conversation_id=conversation_id,
                message_id=message_id,
                task_id=task_id,
                metadata={"answer": full_answer},
            )
        except Exception as exc:
            logger.error("Agent 流式执行失败: %s", exc, exc_info=True)
            yield emit_error(str(exc))
        finally:
            AgentTaskRegistry.unregister(task_id)

    @staticmethod
    def _extract_message_chunk(item: Any):
        payload = item[-1] if isinstance(item, tuple) and item else item
        if isinstance(payload, tuple) and payload:
            return payload[0]
        return payload
