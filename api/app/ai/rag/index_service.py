"""LlamaIndex RAG 索引服务（pgvector）。"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

from llama_index.core import Document, Settings, StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.postgres import PGVectorStore
from sqlalchemy import text as sa_text
from sqlalchemy.orm import Session

from app.ai.models.agent_config import AgentConfig
from app.ai.models.agent_knowledge_base import AgentKnowledgeBase, AgentKnowledgeDocument
from app.ai.runtime.capabilities import AgentCapabilities
from app.common.models.file import File
from app.core.config import get_settings
from app.core.minio_client import get_minio_client

logger = logging.getLogger(__name__)
settings = get_settings()


def _sync_database_url(database_url: str) -> str:
    """LlamaIndex PGVectorStore 需要 psycopg2 同步连接串。"""
    return database_url.replace("postgresql+asyncpg://", "postgresql://")


class RagIndexService:
    """基于 LlamaIndex + pgvector 的知识库索引与检索。"""

    def __init__(self, db: Session):
        self.db = db

    def _ensure_pgvector_extension(self) -> None:
        try:
            self.db.execute(sa_text("CREATE EXTENSION IF NOT EXISTS vector"))
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            raise RuntimeError(
                "RAG 需要 PostgreSQL pgvector 扩展，请在数据库安装 pgvector 后重试。"
                f" 原始错误: {exc}"
            ) from exc

    def _build_embedding(self, agent_config: AgentConfig, kb: AgentKnowledgeBase) -> OpenAIEmbedding:
        return OpenAIEmbedding(
            model=kb.embedding_model,
            api_key=agent_config.api_key,
            api_base=agent_config.base_url or None,
        )

    def _build_vector_store(self, kb: AgentKnowledgeBase) -> PGVectorStore:
        db_url = _sync_database_url(settings.DATABASE_URL)
        parsed = urlparse(db_url.replace("postgresql://", "http://"))
        return PGVectorStore.from_params(
            database=parsed.path.lstrip("/") or "anmeismart",
            host=parsed.hostname or "localhost",
            password=parsed.password,
            port=parsed.port or 5432,
            user=parsed.username or "postgres",
            table_name=kb.index_table_name,
            embed_dim=1536,
            hybrid_search=False,
        )

    def ensure_knowledge_base(
        self,
        *,
        agent_config: AgentConfig,
        capabilities: AgentCapabilities,
        name: str = "default",
    ) -> AgentKnowledgeBase:
        kb_id = capabilities.knowledge_base_id
        if kb_id:
            kb = self.db.query(AgentKnowledgeBase).filter(AgentKnowledgeBase.id == kb_id).first()
            if kb:
                return kb

        table_name = f"agent_rag_{agent_config.id.replace('-', '_')[:20]}"
        kb = AgentKnowledgeBase(
            agent_config_id=agent_config.id,
            name=name,
            embedding_model=capabilities.embedding_model,
            chunk_size=settings.AGENT_RAG_CHUNK_SIZE,
            chunk_overlap=settings.AGENT_RAG_CHUNK_OVERLAP,
            index_table_name=table_name,
            enabled=True,
        )
        self.db.add(kb)
        self.db.commit()
        self.db.refresh(kb)
        return kb

    def index_file(
        self,
        *,
        agent_config: AgentConfig,
        kb: AgentKnowledgeBase,
        file_record: File,
        content_bytes: bytes,
    ) -> AgentKnowledgeDocument:
        doc_record = AgentKnowledgeDocument(
            knowledge_base_id=kb.id,
            file_id=file_record.id,
            name=file_record.file_name,
            status="pending",
        )
        self.db.add(doc_record)
        self.db.commit()
        self.db.refresh(doc_record)

        try:
            self._ensure_pgvector_extension()
            Settings.embed_model = self._build_embedding(agent_config, kb)
            vector_store = self._build_vector_store(kb)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)

            text = content_bytes.decode("utf-8", errors="ignore")
            if not text.strip():
                raise ValueError("文件内容为空或无法解析为文本")

            splitter = SentenceSplitter(chunk_size=kb.chunk_size, chunk_overlap=kb.chunk_overlap)
            nodes = splitter.get_nodes_from_documents(
                [
                    Document(
                        text=text,
                        metadata={
                            "file_id": file_record.id,
                            "file_name": file_record.file_name,
                            "knowledge_base_id": kb.id,
                            "document_id": doc_record.id,
                        },
                    )
                ]
            )

            VectorStoreIndex(nodes, storage_context=storage_context)
            doc_record.status = "indexed"
            doc_record.chunk_count = len(nodes)
            self.db.commit()
            logger.info("RAG 索引完成: kb=%s file=%s chunks=%s", kb.id, file_record.id, len(nodes))
            return doc_record
        except Exception as exc:
            doc_record.status = "failed"
            doc_record.error_message = str(exc)
            self.db.commit()
            logger.error("RAG 索引失败: %s", exc, exc_info=True)
            raise

    def retrieve(self, *, agent_config: AgentConfig, kb: AgentKnowledgeBase, query: str, top_k: Optional[int] = None) -> List[str]:
        self._ensure_pgvector_extension()
        Settings.embed_model = self._build_embedding(agent_config, kb)
        vector_store = self._build_vector_store(kb)
        index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
        retriever = index.as_retriever(similarity_top_k=top_k or settings.AGENT_RAG_TOP_K)
        nodes = retriever.retrieve(query)
        return [node.get_content() for node in nodes]

    def load_file_bytes(self, file_record: File) -> bytes:
        minio = get_minio_client()
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        try:
            minio.client.fget_object(minio.bucket_name, file_record.object_name, tmp_path)
            return Path(tmp_path).read_bytes()
        finally:
            Path(tmp_path).unlink(missing_ok=True)
