from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime, time, timezone
import pytz
from apps.api.models.compliance import DNCEntry, ConsentRecord
from apps.api.repositories.compliance_repo import DNCRepository, ConsentRepository


class ComplianceService:
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.dnc_repo = DNCRepository(session, tenant_id)
        self.consent_repo = ConsentRepository(session, tenant_id)

    async def check_can_call(self, phone_number: str, tenant_id: UUID) -> bool:
        # Re-initialize repos with passed tenant_id if different
        if tenant_id != self.tenant_id:
            dnc_repo = DNCRepository(self.session, tenant_id)
        else:
            dnc_repo = self.dnc_repo

        dnc_entry = await dnc_repo.get_by_phone(phone_number)
        if dnc_entry:
            return False
        return True

    async def add_to_dnc(self, phone_number: str, source: str, reason: str = None) -> DNCEntry:
        existing = await self.dnc_repo.get_by_phone(phone_number)
        if existing:
            return existing
        return await self.dnc_repo.create(
            phone_number=phone_number, source=source, reason=reason, is_active=True
        )

    async def remove_from_dnc(self, phone_number: str) -> bool:
        entry = await self.dnc_repo.get_by_phone(phone_number)
        if entry:
            await self.dnc_repo.update(entry.id, is_active=False)
            return True
        return False

    async def record_consent(
        self,
        phone_number: str,
        consent_type: str,
        status: str,
        source: str,
        contact_id: UUID = None,
    ) -> ConsentRecord:
        now = datetime.now(timezone.utc)
        granted_at = now if status == "granted" else None
        revoked_at = now if status == "revoked" else None

        return await self.consent_repo.create(
            phone_number=phone_number,
            consent_type=consent_type,
            status=status,
            source=source,
            contact_id=contact_id,
            granted_at=granted_at,
            revoked_at=revoked_at,
        )

    def check_calling_hours(
        self, contact_timezone: str, start_time_str: str, end_time_str: str
    ) -> bool:
        try:
            tz = pytz.timezone(contact_timezone)
        except pytz.UnknownTimeZoneError:
            tz = pytz.UTC

        now = datetime.now(tz).time()

        try:
            start_hour, start_min = map(int, start_time_str.split(":"))
            end_hour, end_min = map(int, end_time_str.split(":"))
            start_t = time(start_hour, start_min)
            end_t = time(end_hour, end_min)
        except Exception:
            return False

        if start_t <= end_t:
            return start_t <= now <= end_t
        else:
            return now >= start_t or now <= end_t

    async def import_dnc_list(self, phone_numbers: List[str], source: str = "imported") -> int:
        count = 0
        for phone in phone_numbers:
            existing = await self.dnc_repo.get_by_phone(phone)
            if not existing:
                await self.dnc_repo.create(phone_number=phone, source=source, is_active=True)
                count += 1
        return count
