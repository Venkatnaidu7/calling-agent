from uuid import UUID
from typing import TypeVar, Generic, Type, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from sqlalchemy.engine.result import ScalarResult
from apps.api.schemas.common import PaginationParams
from apps.api.database import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession, tenant_id: UUID | None = None):
        self.model = model
        self.session = session
        self.tenant_id = tenant_id
    
    def _apply_tenant_filter(self, stmt, model_cls=None):
        """Apply tenant filter to any query. All tenant-scoped queries MUST use this."""
        model_cls = model_cls or self.model
        if self.tenant_id and hasattr(model_cls, 'tenant_id'):
            stmt = stmt.where(model_cls.tenant_id == self.tenant_id)
        return stmt

    async def get_by_id(self, id: UUID | str) -> ModelType | None:
        stmt = select(self.model).where(self.model.id == id)
        stmt = self._apply_tenant_filter(stmt)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, pagination: PaginationParams) -> tuple[list[ModelType], int]:
        count_stmt = select(func.count()).select_from(self.model)
        count_stmt = self._apply_tenant_filter(count_stmt)
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = select(self.model)
        stmt = self._apply_tenant_filter(stmt)
        
        # Determine sorting
        order_col = getattr(self.model, pagination.sort_by, self.model.created_at)
        if pagination.sort_order.lower() == "desc":
            stmt = stmt.order_by(order_col.desc())
        else:
            stmt = stmt.order_by(order_col.asc())
            
        stmt = stmt.offset(pagination.skip).limit(pagination.limit)
        
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())
        
        return items, total

    async def create(self, **kwargs) -> ModelType:
        if self.tenant_id and hasattr(self.model, 'tenant_id') and 'tenant_id' not in kwargs:
            kwargs['tenant_id'] = self.tenant_id
            
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, id: UUID | str, **kwargs) -> ModelType | None:
        stmt = update(self.model).where(self.model.id == id)
        stmt = self._apply_tenant_filter(stmt)
        stmt = stmt.values(**kwargs).returning(self.model)
        
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one_or_none()

    async def delete(self, id: UUID | str) -> bool:
        stmt = delete(self.model).where(self.model.id == id)
        stmt = self._apply_tenant_filter(stmt)
        
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0
