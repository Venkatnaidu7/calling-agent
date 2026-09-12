from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from apps.api.models.contact import Contact, ContactList
from apps.api.schemas.contact import ContactCreate, ContactUpdate, ContactListCreate
from apps.api.schemas.common import PaginationParams
from apps.api.repositories.contact_repo import (
    ContactRepository,
    ContactListRepository,
    ContactListMemberRepository,
)


class ContactService:
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.contact_repo = ContactRepository(session, tenant_id)
        self.list_repo = ContactListRepository(session, tenant_id)
        self.member_repo = ContactListMemberRepository(session, tenant_id)

    async def get_contact(self, contact_id: UUID) -> Contact:
        contact = await self.contact_repo.get_by_id(contact_id)
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        return contact

    async def create_contact(self, data: ContactCreate) -> Contact:
        existing = await self.contact_repo.get_by_phone(data.phone_number)
        if existing:
            raise HTTPException(status_code=400, detail="Contact with phone number already exists")
        return await self.contact_repo.create(**data.model_dump())

    async def update_contact(self, contact_id: UUID, data: ContactUpdate) -> Contact:
        contact = await self.contact_repo.update(contact_id, **data.model_dump(exclude_unset=True))
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        return contact

    async def list_contacts(self, pagination: PaginationParams):
        return await self.contact_repo.get_all(pagination)

    async def create_list(self, data: ContactListCreate) -> ContactList:
        return await self.list_repo.create(**data.model_dump())

    async def add_to_list(self, contact_list_id: UUID, contact_id: UUID):
        return await self.member_repo.add_contact_to_list(contact_list_id, contact_id)

    async def remove_from_list(self, contact_list_id: UUID, contact_id: UUID):
        return await self.member_repo.remove_contact_from_list(contact_list_id, contact_id)
