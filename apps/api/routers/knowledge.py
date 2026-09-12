import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.database import get_db
from apps.api.dependencies import get_tenant_context as get_current_user_tenant_id, require_roles, require_permissions
from apps.api.schemas.knowledge import (
    KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseResponse,
    DocumentUpload, DocumentResponse, SearchRequest, SearchResult
)
from apps.api.services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/knowledge-bases", tags=["Knowledge"])

def get_knowledge_service(
    session: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_current_user_tenant_id)
) -> KnowledgeService:
    return KnowledgeService(session, tenant_id)

@router.get("", response_model=List[KnowledgeBaseResponse])
async def list_knowledge_bases(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    service: KnowledgeService = Depends(get_knowledge_service),
    _ = Depends(require_permissions("view_all"))
):
    return await service.list_knowledge_bases(skip=skip, limit=limit)

@router.post("", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(
    data: KnowledgeBaseCreate,
    service: KnowledgeService = Depends(get_knowledge_service),
    _ = Depends(require_roles("TENANT_ADMIN", "TENANT_OWNER"))
):
    return await service.create_knowledge_base(data)

@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    kb_id: uuid.UUID,
    service: KnowledgeService = Depends(get_knowledge_service)
):
    return await service.get_knowledge_base(kb_id)

@router.put("/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    kb_id: uuid.UUID,
    data: KnowledgeBaseUpdate,
    service: KnowledgeService = Depends(get_knowledge_service),
    _ = Depends(require_roles("TENANT_ADMIN", "TENANT_OWNER"))
):
    return await service.update_knowledge_base(kb_id, data)

@router.delete("/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base(
    kb_id: uuid.UUID,
    service: KnowledgeService = Depends(get_knowledge_service),
    _ = Depends(require_roles("TENANT_ADMIN", "TENANT_OWNER"))
):
    await service.delete_knowledge_base(kb_id)

@router.get("/{kb_id}/documents", response_model=List[DocumentResponse])
async def list_documents(
    kb_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    service: KnowledgeService = Depends(get_knowledge_service)
):
    return await service.list_documents(kb_id, skip=skip, limit=limit)

@router.post("/{kb_id}/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    kb_id: uuid.UUID,
    data: DocumentUpload,
    service: KnowledgeService = Depends(get_knowledge_service),
    _ = Depends(require_roles("TENANT_ADMIN", "TENANT_OWNER"))
):
    return await service.add_document(kb_id, data)

@router.get("/{kb_id}/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(
    kb_id: uuid.UUID,
    doc_id: uuid.UUID,
    service: KnowledgeService = Depends(get_knowledge_service)
):
    return await service.get_document(kb_id, doc_id)

@router.delete("/{kb_id}/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    kb_id: uuid.UUID,
    doc_id: uuid.UUID,
    service: KnowledgeService = Depends(get_knowledge_service),
    _ = Depends(require_roles("TENANT_ADMIN", "TENANT_OWNER"))
):
    await service.delete_document(kb_id, doc_id)

@router.post("/{kb_id}/documents/{doc_id}/process", response_model=DocumentResponse)
async def process_document(
    kb_id: uuid.UUID,
    doc_id: uuid.UUID,
    service: KnowledgeService = Depends(get_knowledge_service),
    _ = Depends(require_roles("TENANT_ADMIN", "TENANT_OWNER"))
):
    return await service.process_document(kb_id, doc_id)

@router.post("/{kb_id}/search", response_model=SearchResult)
async def search_knowledge_base(
    kb_id: uuid.UUID,
    data: SearchRequest,
    service: KnowledgeService = Depends(get_knowledge_service)
):
    if kb_id != data.knowledge_base_id:
        raise HTTPException(status_code=400, detail="Path kb_id must match request body knowledge_base_id")
    return await service.search(kb_id, data.query, max_results=data.max_results, min_relevance=data.min_relevance)
