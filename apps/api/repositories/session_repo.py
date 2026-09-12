from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from apps.api.models import UserSession
from apps.api.repositories.base import BaseRepository

class SessionRepository(BaseRepository[UserSession]):
    def __init__(self, session: AsyncSession):
        super().__init__(model=UserSession, session=session, tenant_id=None)

    async def get_by_refresh_token_hash(self, refresh_token_hash: str) -> UserSession | None:
        stmt = select(UserSession).where(UserSession.refresh_token_hash == refresh_token_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke(self, session_id: UUID) -> None:
        now = datetime.now(timezone.utc)
        stmt = update(UserSession).where(UserSession.id == session_id).values(revoked_at=now)
        await self.session.execute(stmt)
        await self.session.flush()

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        now = datetime.now(timezone.utc)
        stmt = update(UserSession).where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None)).values(revoked_at=now)
        await self.session.execute(stmt)
        await self.session.flush()

    async def cleanup_expired(self) -> int:
        now = datetime.now(timezone.utc)
        stmt = delete(UserSession).where(UserSession.expires_at < now)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount
