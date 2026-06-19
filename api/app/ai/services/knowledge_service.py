"""Agent 知识库管理服务。"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.ai.models.agent_config import AgentConfig
from app.ai.models.agent_knowledge_base import AgentKnowledgeBase, AgentKnowledgeDocument
from app.ai.rag.index_service import RagIndexService
from app.ai.runtime.capabilities import AgentCapabilities
from app.common.models.file import File

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AgentKnowledgeService:
    def __init__(self, db: Session):
        self.db = db
        self.rag = RagIndexService(db)

    def _load_agent(self, agent_config_id: str) -> AgentConfig:
        config = (
            self.db.query(AgentConfig)
            .filter(AgentConfig.id == agent_config_id, AgentConfig.enabled.is_(True))
            .first()
        )
        if not config:
            raise ValueError(f"Agent 配置不存在或未启用: {agent_config_id}")
        return config

    def list_knowledge_bases(self, agent_config_id: str) -> List[AgentKnowledgeBase]:
        self._load_agent(agent_config_id)
        return (
            self.db.query(AgentKnowledgeBase)
            .filter(AgentKnowledgeBase.agent_config_id == agent_config_id)
            .order_by(AgentKnowledgeBase.created_at.desc())
            .all()
        )

    def list_documents(self, agent_config_id: str, knowledge_base_id: str) -> List[AgentKnowledgeDocument]:
        self._load_agent(agent_config_id)
        kb = (
            self.db.query(AgentKnowledgeBase)
            .filter(
                AgentKnowledgeBase.id == knowledge_base_id,
                AgentKnowledgeBase.agent_config_id == agent_config_id,
            )
            .first()
        )
        if not kb:
            raise ValueError("知识库不存在")
        return (
            self.db.query(AgentKnowledgeDocument)
            .filter(AgentKnowledgeDocument.knowledge_base_id == knowledge_base_id)
            .order_by(AgentKnowledgeDocument.created_at.desc())
            .all()
        )

    def create_knowledge_base(
        self,
        *,
        agent_config_id: str,
        name: str,
        description: Optional[str] = None,
        link_to_agent: bool = True,
    ) -> AgentKnowledgeBase:
        import uuid as uuid_lib

        config = self._load_agent(agent_config_id)
        caps = AgentCapabilities.from_agent_config(config.app_name, config.capabilities)
        table_suffix = uuid_lib.uuid4().hex[:8]
        table_name = f"agent_rag_{agent_config_id.replace('-', '_')[:12]}_{table_suffix}"

        kb = AgentKnowledgeBase(
            agent_config_id=agent_config_id,
            name=name,
            description=description,
            embedding_model=caps.embedding_model,
            chunk_size=settings.AGENT_RAG_CHUNK_SIZE,
            chunk_overlap=settings.AGENT_RAG_CHUNK_OVERLAP,
            index_table_name=table_name,
            enabled=True,
        )
        self.db.add(kb)
        if link_to_agent:
            merged = dict(config.capabilities or {})
            merged["enable_rag"] = True
            merged["knowledge_base_id"] = kb.id
            config.capabilities = merged
        self.db.commit()
        self.db.refresh(kb)
        return kb

    def index_uploaded_file(
        self,
        *,
        agent_config_id: str,
        knowledge_base_id: str,
        file_id: str,
    ) -> AgentKnowledgeDocument:
        config = self._load_agent(agent_config_id)
        kb = (
            self.db.query(AgentKnowledgeBase)
            .filter(
                AgentKnowledgeBase.id == knowledge_base_id,
                AgentKnowledgeBase.agent_config_id == agent_config_id,
            )
            .first()
        )
        if not kb:
            raise ValueError("知识库不存在")

        file_record = self.db.query(File).filter(File.id == file_id).first()
        if not file_record:
            raise ValueError("文件不存在")

        content = self.rag.load_file_bytes(file_record)
        return self.rag.index_file(
            agent_config=config,
            kb=kb,
            file_record=file_record,
            content_bytes=content,
        )

    @staticmethod
    def serialize_kb(kb: AgentKnowledgeBase) -> Dict[str, Any]:
        return {
            "id": kb.id,
            "agent_config_id": kb.agent_config_id,
            "name": kb.name,
            "description": kb.description,
            "embedding_model": kb.embedding_model,
            "chunk_size": kb.chunk_size,
            "chunk_overlap": kb.chunk_overlap,
            "enabled": kb.enabled,
            "index_table_name": kb.index_table_name,
            "created_at": kb.created_at.isoformat() if kb.created_at else None,
        }

    @staticmethod
    def serialize_doc(doc: AgentKnowledgeDocument) -> Dict[str, Any]:
        return {
            "id": doc.id,
            "knowledge_base_id": doc.knowledge_base_id,
            "file_id": doc.file_id,
            "name": doc.name,
            "status": doc.status,
            "chunk_count": doc.chunk_count,
            "error_message": doc.error_message,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
        }
