import uuid
from typing import Sequence
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from apps.api.models.knowledge import KnowledgeBase, KnowledgeDocument
from apps.api.schemas.knowledge import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    DocumentUpload,
    SearchResult,
    ChunkResponse,
)
from apps.api.repositories.knowledge_repo import (
    KnowledgeBaseRepository,
    KnowledgeDocumentRepository,
    KnowledgeChunkRepository,
)
from apps.api.services.embedding_service import EmbeddingService
from apps.api.services.document_processor import DocumentProcessor


class KnowledgeService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.kb_repo = KnowledgeBaseRepository(session)
        self.doc_repo = KnowledgeDocumentRepository(session)
        self.chunk_repo = KnowledgeChunkRepository(session)
        self.embedding_service = EmbeddingService()
        self.document_processor = DocumentProcessor()

    async def create_knowledge_base(self, data: KnowledgeBaseCreate) -> KnowledgeBase:
        kb = await self.kb_repo.create(
            tenant_id=self.tenant_id,
            name=data.name,
            description=data.description,
            agent_id=data.agent_id,
        )
        return kb

    async def list_knowledge_bases(
        self, skip: int = 0, limit: int = 100
    ) -> Sequence[KnowledgeBase]:
        return await self.kb_repo.get_all(tenant_id=self.tenant_id, skip=skip, limit=limit)

    async def get_knowledge_base(self, kb_id: uuid.UUID) -> KnowledgeBase:
        kb = await self.kb_repo.get(tenant_id=self.tenant_id, id=kb_id)
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        return kb

    async def update_knowledge_base(
        self, kb_id: uuid.UUID, data: KnowledgeBaseUpdate
    ) -> KnowledgeBase:
        await self.get_knowledge_base(kb_id)
        update_data = data.model_dump(exclude_unset=True)
        return await self.kb_repo.update(tenant_id=self.tenant_id, id=kb_id, **update_data)

    async def delete_knowledge_base(self, kb_id: uuid.UUID) -> None:
        await self.get_knowledge_base(kb_id)
        await self.kb_repo.delete(tenant_id=self.tenant_id, id=kb_id)

    async def add_document(self, kb_id: uuid.UUID, data: DocumentUpload) -> KnowledgeDocument:
        kb = await self.get_knowledge_base(kb_id)

        doc = await self.doc_repo.create(
            tenant_id=self.tenant_id,
            knowledge_base_id=kb.id,
            title=data.title,
            source_type=data.source_type,
            content=data.content,
            source_url=data.source_url,
            status="pending",
        )

        # Increment document count on KB
        await self.kb_repo.update(
            tenant_id=self.tenant_id, id=kb.id, document_count=kb.document_count + 1
        )

        return doc

    async def get_document(self, kb_id: uuid.UUID, doc_id: uuid.UUID) -> KnowledgeDocument:
        doc = await self.doc_repo.get(tenant_id=self.tenant_id, id=doc_id)
        if not doc or doc.knowledge_base_id != kb_id:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc

    async def list_documents(
        self, kb_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[KnowledgeDocument]:
        return await self.doc_repo.get_all(
            tenant_id=self.tenant_id, knowledge_base_id=kb_id, skip=skip, limit=limit
        )

    async def delete_document(self, kb_id: uuid.UUID, doc_id: uuid.UUID) -> None:
        doc = await self.get_document(kb_id, doc_id)
        kb = await self.get_knowledge_base(kb_id)

        chunk_count = doc.chunk_count

        await self.doc_repo.delete(tenant_id=self.tenant_id, id=doc_id)

        await self.kb_repo.update(
            tenant_id=self.tenant_id,
            id=kb.id,
            document_count=max(0, kb.document_count - 1),
            chunk_count=max(0, kb.chunk_count - chunk_count),
        )

    async def process_document(self, kb_id: uuid.UUID, doc_id: uuid.UUID) -> KnowledgeDocument:
        doc = await self.get_document(kb_id, doc_id)
        kb = await self.get_knowledge_base(kb_id)

        doc = await self.doc_repo.update(tenant_id=self.tenant_id, id=doc_id, status="processing")

        try:
            # 1. Extract text
            content_to_process = doc.content or doc.source_url
            if not content_to_process:
                raise ValueError("No content or source URL provided")

            raw_text = await self.document_processor.extract_text(
                content_to_process, doc.source_type
            )

            # 2. Chunk text
            chunks_text = self.embedding_service.chunk_text(raw_text)

            # 3. Delete existing chunks if reprocessing
            await self.chunk_repo.delete_by_document(self.tenant_id, doc.id)

            # 4. Generate embeddings in batches
            batch_size = 100
            for i in range(0, len(chunks_text), batch_size):
                batch = chunks_text[i : i + batch_size]
                embeddings = await self.embedding_service.generate_embeddings_batch(batch)

                for j, (chunk_text, embedding) in enumerate(zip(batch, embeddings, strict=False)):
                    await self.chunk_repo.create(
                        tenant_id=self.tenant_id,
                        document_id=doc.id,
                        knowledge_base_id=kb.id,
                        content=chunk_text,
                        embedding=embedding,
                        chunk_index=i + j,
                        token_count=self.embedding_service.count_tokens(chunk_text),
                    )

            # Update counts
            total_chunks = len(chunks_text)

            # Recalculate KB chunk count (subtract old doc chunk count if any, add new)
            old_chunk_count = doc.chunk_count
            new_kb_chunk_count = max(0, kb.chunk_count - old_chunk_count) + total_chunks

            await self.kb_repo.update(
                tenant_id=self.tenant_id, id=kb.id, chunk_count=new_kb_chunk_count
            )

            doc = await self.doc_repo.update(
                tenant_id=self.tenant_id,
                id=doc_id,
                status="completed",
                chunk_count=total_chunks,
                processed_at=datetime.utcnow(),
            )
            return doc

        except Exception as e:
            doc = await self.doc_repo.update(
                tenant_id=self.tenant_id, id=doc_id, status="failed", error_message=str(e)
            )
            raise

    async def search(
        self, kb_id: uuid.UUID, query: str, max_results: int = 5, min_relevance: float = 0.7
    ) -> SearchResult:
        await self.get_knowledge_base(kb_id)

        query_embedding = await self.embedding_service.generate_embedding(query)
        results = await self.chunk_repo.search_similar(
            tenant_id=self.tenant_id,
            knowledge_base_id=kb_id,
            embedding=query_embedding,
            limit=max_results,
            min_similarity=min_relevance,
        )

        chunks = [
            ChunkResponse(
                id=chunk.id,
                content=chunk.content,
                chunk_index=chunk.chunk_index,
                token_count=chunk.token_count,
                relevance_score=score,
            )
            for chunk, score in results
        ]

        return SearchResult(query=query, chunks=chunks)
