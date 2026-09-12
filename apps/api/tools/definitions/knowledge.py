import uuid
from typing import Any
import structlog
from apps.api.tools.registry import ToolRegistry, ToolDefinition
from apps.api.database import async_session_factory
from apps.api.services.knowledge_service import KnowledgeService

logger = structlog.get_logger()


async def query_knowledge_base(
    query: str,
    _context: dict = None,
    **kwargs
) -> dict[str, Any]:
    """
    Search the company knowledge base for policy, product, pricing, or FAQ information.
    Call this whenever a customer asks a factual question you need to verify.
    """
    tenant_id_str = _context.get("tenant_id") if _context else None
    logger.info("rag_knowledge_query", query=query, tenant_id=tenant_id_str)

    if not tenant_id_str:
        return {"found": False, "information": "No company knowledge base attached."}

    try:
        tenant_uuid = uuid.UUID(tenant_id_str)
        async with async_session_factory() as session:
            service = KnowledgeService(session, tenant_id=tenant_uuid)
            
            # Find the active knowledge base for this tenant
            kbs = await service.list_knowledge_bases()
            if not kbs:
                return {"found": False, "information": "No knowledge documents found."}

            kb_id = kbs[0].id  # primary knowledge base
            result = await service.search(query=query, kb_id=kb_id, max_results=3, min_relevance=0.6)

            if not result.chunks:
                return {"found": False, "information": f"No specific documentation found regarding: {query}"}

            excerpts = "\n---\n".join(c.content for c in result.chunks)
            return {
                "found": True,
                "information": excerpts,
                "message": "Retrieved authoritative documentation from company knowledge base."
            }
    except Exception as e:
        logger.error("rag_query_error", error=str(e), query=query)
        return {"found": False, "error": str(e)}


def register_knowledge_tools():
    ToolRegistry.register(ToolDefinition(
        name="query_knowledge_base",
        description="Search company knowledge documents, manuals, pricing sheets, and policies for verified facts.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Specific search query, e.g. 'cancellation policy' or 'office weekend hours'",
                },
            },
            "required": ["query"],
        },
        handler=query_knowledge_base,
        category="knowledge",
    ))
