from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from apps.api.models import AuditLog
from apps.api.schemas.common import PaginationParams
from apps.api.repositories.base import BaseRepository

class AuditRepository(BaseRepository[AuditLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(model=AuditLog, session=session, tenant_id=None)

    async def list_by_tenant(self, tenant_id: UUID, pagination: PaginationParams, filters: dict = None) -> tuple[list[AuditLog], int]:
        filters = filters or {}
        stmt = select(AuditLog).where(AuditLog.tenant_id == tenant_id)
        
        # Apply extra filters if provided
        for key, value in filters.items():
            if hasattr(AuditLog, key) and value is not None:
                stmt = stmt.where(getattr(AuditLog, key) == value)
                
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one()
        
        # Pagination and order
        order_col = getattr(AuditLog, pagination.sort_by, AuditLog.created_at)
        if pagination.sort_order.lower() == "desc":
            stmt = stmt.order_by(order_col.desc())
        else:
            stmt = stmt.order_by(order_col.asc())
            
        stmt = stmt.offset(pagination.skip).limit(pagination.limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def list_all(self, pagination: PaginationParams, filters: dict = None) -> tuple[list[AuditLog], int]:
        filters = filters or {}
        stmt = select(AuditLog)
        
        # Apply extra filters if provided
        for key, value in filters.items():
            if hasattr(AuditLog, key) and value is not None:
                stmt = stmt.where(getattr(AuditLog, key) == value)
                
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one()
        
        order_col = getattr(AuditLog, pagination.sort_by, AuditLog.created_at)
        if pagination.sort_order.lower() == "desc":
            stmt = stmt.order_by(order_col.desc())
        else:
            stmt = stmt.order_by(order_col.asc())
            
        stmt = stmt.offset(pagination.skip).limit(pagination.limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total
