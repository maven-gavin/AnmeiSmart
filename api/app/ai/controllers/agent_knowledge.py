"""Agent 知识库（RAG）管理接口。"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.ai.schemas.knowledge import (
    KnowledgeBaseCreate,
    KnowledgeBaseInfo,
    KnowledgeBaseListResponse,
    KnowledgeDocumentIndexRequest,
    KnowledgeDocumentInfo,
    KnowledgeDocumentResponse,
)
from app.ai.services.knowledge_service import AgentKnowledgeService
from app.common.deps import get_db
from app.identity_access.deps import get_current_admin

logger = logging.getLogger(__name__)
router = APIRouter()


def _kb_info(data: dict) -> KnowledgeBaseInfo:
    return KnowledgeBaseInfo(**data)


@router.get("/{agent_config_id}/knowledge-bases", response_model=KnowledgeBaseListResponse)
def list_knowledge_bases(
    agent_config_id: str,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    service = AgentKnowledgeService(db)
    try:
        items = [_kb_info(service.serialize_kb(kb)) for kb in service.list_knowledge_bases(agent_config_id)]
        return KnowledgeBaseListResponse(items=items)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/{agent_config_id}/knowledge-bases", response_model=KnowledgeBaseInfo)
def create_knowledge_base(
    agent_config_id: str,
    body: KnowledgeBaseCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    service = AgentKnowledgeService(db)
    try:
        kb = service.create_knowledge_base(
            agent_config_id=agent_config_id,
            name=body.name,
            description=body.description,
            link_to_agent=body.link_to_agent,
        )
        return _kb_info(service.serialize_kb(kb))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


@router.post(
    "/{agent_config_id}/knowledge-bases/{knowledge_base_id}/documents",
    response_model=KnowledgeDocumentResponse,
)
def index_document(
    agent_config_id: str,
    knowledge_base_id: str,
    body: KnowledgeDocumentIndexRequest,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    service = AgentKnowledgeService(db)
    try:
        doc = service.index_uploaded_file(
            agent_config_id=agent_config_id,
            knowledge_base_id=knowledge_base_id,
            file_id=body.file_id,
        )
        return KnowledgeDocumentResponse(document=KnowledgeDocumentInfo(**service.serialize_doc(doc)))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
