import uuid
from typing import List, Sequence
from sqlalchemy import select, delete, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.models.knowledge import KnowledgeBase, KnowledgeDocument, KnowledgeChunk
from apps.api.repositories.base import BaseRepository

class KnowledgeBaseRepository(BaseRepository[KnowledgeBase]):
    def __init__(self, session: AsyncSession):
        super().__init__(KnowledgeBase, session)

class KnowledgeDocumentRepository(BaseRepository[KnowledgeDocument]):
    def __init__(self, session: AsyncSession):
        super().__init__(KnowledgeDocument, session)

class KnowledgeChunkRepository(BaseRepository[KnowledgeChunk]):
    def __init__(self, session: AsyncSession):
        super().__init__(KnowledgeChunk, session)
        
    async def get_by_document(self, tenant_id: uuid.UUID, document_id: uuid.UUID) -> Sequence[KnowledgeChunk]:
        stmt = select(self.model_class).where(
            self.model_class.tenant_id == tenant_id,
            self.model_class.document_id == document_id
        ).order_by(asc(self.model_class.chunk_index))
        result = await self.session.execute(stmt)
        return result.scalars().all()
        
    async def delete_by_document(self, tenant_id: uuid.UUID, document_id: uuid.UUID) -> None:
        stmt = delete(self.model_class).where(
            self.model_class.tenant_id == tenant_id,
            self.model_class.document_id == document_id
        )
        await self.session.execute(stmt)
        
    async def search_similar(self, tenant_id: uuid.UUID, knowledge_base_id: uuid.UUID, embedding: list[float], limit: int = 5, min_similarity: float = 0.7) -> Sequence[tuple[KnowledgeChunk, float]]:
        # Using cosine distance: 1 - cosine_distance = cosine_similarity
        distance = self.model_class.embedding.cosine_distance(embedding)
        similarity = 1 - distance
        
        stmt = select(self.model_class, similarity.label("relevance_score")).where(
            self.model_class.tenant_id == tenant_id,
            self.model_class.knowledge_base_id == knowledge_base_id,
            similarity >= min_similarity
        ).order_by(desc("relevance_score")).limit(limit)
        
        result = await self.session.execute(stmt)
        return result.all()
