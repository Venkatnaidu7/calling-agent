from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from apps.api.models.contact import Contact, ContactList, ContactListMember
from apps.api.repositories.base import BaseRepository


class ContactRepository(BaseRepository[Contact]):
    def __init__(self, session: AsyncSession, tenant_id: UUID | None = None):
        super().__init__(Contact, session, tenant_id)

    async def get_by_phone(self, phone_number: str) -> Contact | None:
        stmt = select(self.model).where(self.model.phone_number == phone_number)
        stmt = self._apply_tenant_filter(stmt)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class ContactListRepository(BaseRepository[ContactList]):
    def __init__(self, session: AsyncSession, tenant_id: UUID | None = None):
        super().__init__(ContactList, session, tenant_id)


class ContactListMemberRepository(BaseRepository[ContactListMember]):
    def __init__(self, session: AsyncSession, tenant_id: UUID | None = None):
        super().__init__(ContactListMember, session, tenant_id)

    async def add_contact_to_list(
        self, contact_list_id: UUID, contact_id: UUID
    ) -> ContactListMember:
        member = ContactListMember(
            tenant_id=self.tenant_id, contact_list_id=contact_list_id, contact_id=contact_id
        )
        self.session.add(member)
        await self.session.flush()

        # update list count
        stmt = select(ContactList).where(ContactList.id == contact_list_id)
        stmt = self._apply_tenant_filter(stmt, ContactList)
        lst = (await self.session.execute(stmt)).scalar_one_or_none()
        if lst:
            lst.contact_count += 1

        return member

    async def remove_contact_from_list(self, contact_list_id: UUID, contact_id: UUID) -> bool:
        stmt = delete(self.model).where(
            self.model.contact_list_id == contact_list_id, self.model.contact_id == contact_id
        )
        stmt = self._apply_tenant_filter(stmt)
        res = await self.session.execute(stmt)
        await self.session.flush()

        if res.rowcount > 0:
            stmt2 = select(ContactList).where(ContactList.id == contact_list_id)
            stmt2 = self._apply_tenant_filter(stmt2, ContactList)
            lst = (await self.session.execute(stmt2)).scalar_one_or_none()
            if lst and lst.contact_count > 0:
                lst.contact_count -= 1
            return True
        return False
