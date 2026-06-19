"""RAG 检索工具（LangChain Tool）。"""

from __future__ import annotations

from langchain_core.tools import tool
from sqlalchemy.orm import Session

from app.ai.models.agent_config import AgentConfig
from app.ai.models.agent_knowledge_base import AgentKnowledgeBase
from app.ai.rag.index_service import RagIndexService


def build_rag_tool(db: Session, agent_config: AgentConfig, kb: AgentKnowledgeBase):
    rag_service = RagIndexService(db)

    @tool("knowledge_retrieval")
    def knowledge_retrieval(query: str) -> str:
        """从 Agent 知识库检索与问题相关的上下文。"""
        chunks = rag_service.retrieve(agent_config=agent_config, kb=kb, query=query)
        if not chunks:
            return "未找到相关知识。"
        return "\n\n---\n\n".join(chunks)

    return knowledge_retrieval
