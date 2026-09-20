from uuid import UUID
from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.schemas.common import PaginationParams, PaginatedResponse
from apps.api.repositories.audit_repo import AuditRepository


class AuditService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.audit_repo = AuditRepository(session)

    async def log(
        self,
        tenant_id: UUID | None,
        user_id: UUID | None,
        action: str,
        resource_type: str,
        resource_id: UUID,
        details: Dict[str, Any] = None,
        ip: str = None,
    ) -> None:
        """Fire and forget audit log creation. Usually called and awaited, but could be backgrounded."""
        try:
            await self.audit_repo.create(
                tenant_id=tenant_id,
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details or {},
                ip_address=ip,
            )
            # The caller handles the commit
        except Exception:
            # We don't want audit failures to break main workflows, log to stderr/logger in a real app
            pass

    async def list_logs(
        self, tenant_id: UUID, pagination: PaginationParams, filters: dict = None
    ) -> PaginatedResponse:
        items, total = await self.audit_repo.list_by_tenant(tenant_id, pagination, filters)

        # Pydantic schema for audit log would be used here, assume a dict for now if not defined explicitly
        return PaginatedResponse(
            items=[
                {
                    "id": str(i.id),
                    "tenant_id": str(i.tenant_id),
                    "user_id": str(i.user_id) if i.user_id else None,
                    "action": i.action,
                    "resource_type": i.resource_type,
                    "resource_id": str(i.resource_id) if i.resource_id else None,
                    "details": i.details,
                    "ip_address": i.ip_address,
                    "created_at": i.created_at,
                }
                for i in items
            ],
            total=total,
            page=pagination.page,
            per_page=pagination.per_page,
            pages=(total + pagination.per_page - 1) // pagination.per_page if pagination.per_page else 1,
        )
