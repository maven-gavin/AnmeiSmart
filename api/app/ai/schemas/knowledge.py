"""Agent 知识库 API Schema。"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    link_to_agent: bool = Field(True, description="创建后自动绑定到 Agent capabilities")


class KnowledgeBaseInfo(BaseModel):
    id: str
    agent_config_id: str
    name: str
    description: Optional[str] = None
    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    enabled: bool
    index_table_name: str
    created_at: Optional[str] = None


class KnowledgeDocumentIndexRequest(BaseModel):
    file_id: str = Field(..., description="files 表中的文件 ID")


class KnowledgeDocumentInfo(BaseModel):
    id: str
    knowledge_base_id: str
    file_id: Optional[str] = None
    name: str
    status: str
    chunk_count: int
    error_message: Optional[str] = None
    created_at: Optional[str] = None


class KnowledgeBaseListResponse(BaseModel):
    items: List[KnowledgeBaseInfo]


class KnowledgeDocumentResponse(BaseModel):
    document: KnowledgeDocumentInfo
