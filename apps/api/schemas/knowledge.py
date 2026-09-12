from pydantic import BaseModel, Field, UUID4
from typing import Optional, List
from datetime import datetime


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    agent_id: Optional[UUID4] = None


class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    agent_id: Optional[UUID4] = None


class KnowledgeBaseResponse(BaseModel):
    id: UUID4
    name: str
    description: Optional[str]
    agent_id: Optional[UUID4]
    status: str
    document_count: int
    chunk_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentUpload(BaseModel):
    title: str = Field(..., max_length=500)
    source_type: str = Field(..., pattern="^(text|pdf|docx|url|csv)$")
    content: Optional[str] = None
    source_url: Optional[str] = None


class DocumentResponse(BaseModel):
    id: UUID4
    title: str
    source_type: str
    status: str
    chunk_count: int
    file_size_bytes: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


class ChunkResponse(BaseModel):
    id: UUID4
    content: str
    chunk_index: int
    token_count: int
    relevance_score: Optional[float] = None

    model_config = {"from_attributes": True}


class SearchRequest(BaseModel):
    query: str
    knowledge_base_id: UUID4
    max_results: int = 5
    min_relevance: float = 0.7


class SearchResult(BaseModel):
    query: str
    chunks: List[ChunkResponse]
