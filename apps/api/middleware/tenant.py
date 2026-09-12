from uuid import UUID
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.models import User
from apps.api.database import get_db, set_tenant_context
from apps.api.middleware.auth import get_current_user


async def get_tenant_context(
    current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)
) -> UUID:
    """Gets tenant ID from current user and sets the RLS context in DB session."""
    tenant_id = current_user.tenant_id
    await set_tenant_context(session, tenant_id)
    return tenant_id
