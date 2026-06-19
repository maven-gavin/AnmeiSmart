from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship

from app.common.models.base_model import BaseModel
from app.common.deps.uuid_utils import generate_agent_knowledge_base_id, generate_uuid


class AgentKnowledgeBase(BaseModel):
    """Agent 知识库（LlamaIndex RAG）。"""

    __tablename__ = "agent_knowledge_bases"
    __table_args__ = (
        Index("idx_agent_kb_config", "agent_config_id"),
        {"comment": "Agent 知识库表"},
    )

    id = Column(String(36), primary_key=True, default=generate_agent_knowledge_base_id, comment="知识库ID")
    agent_config_id = Column(String(36), ForeignKey("agent_configs.id", ondelete="CASCADE"), nullable=False, comment="Agent配置ID")
    name = Column(String(255), nullable=False, comment="知识库名称")
    description = Column(Text, nullable=True, comment="描述")
    embedding_model = Column(String(100), nullable=False, default="text-embedding-3-small", comment="Embedding模型")
    chunk_size = Column(Integer, nullable=False, default=512, comment="分块大小")
    chunk_overlap = Column(Integer, nullable=False, default=64, comment="分块重叠")
    enabled = Column(Boolean, default=True, nullable=False, comment="是否启用")
    index_table_name = Column(String(100), nullable=False, comment="pgvector 表名")

    documents = relationship("AgentKnowledgeDocument", back_populates="knowledge_base", cascade="all, delete-orphan")


class AgentKnowledgeDocument(BaseModel):
    """知识库文档索引记录。"""

    __tablename__ = "agent_knowledge_documents"
    __table_args__ = (
        Index("idx_agent_kdoc_kb", "knowledge_base_id"),
        {"comment": "Agent 知识库文档表"},
    )

    id = Column(String(36), primary_key=True, default=generate_uuid, comment="文档记录ID")
    knowledge_base_id = Column(String(36), ForeignKey("agent_knowledge_bases.id", ondelete="CASCADE"), nullable=False, comment="知识库ID")
    file_id = Column(String(36), ForeignKey("files.id", ondelete="SET NULL"), nullable=True, comment="关联文件ID")
    name = Column(String(255), nullable=False, comment="文档名称")
    status = Column(String(20), nullable=False, default="pending", comment="pending|indexed|failed")
    chunk_count = Column(Integer, nullable=False, default=0, comment="分块数量")
    error_message = Column(Text, nullable=True, comment="失败原因")
    doc_metadata = Column("metadata", JSON, nullable=True, comment="文档元数据")

    knowledge_base = relationship("AgentKnowledgeBase", back_populates="documents")
