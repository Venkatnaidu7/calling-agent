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

    async def delete_contact(self, contact_id: UUID) -> bool:
        deleted = await self.contact_repo.delete(contact_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Contact not found")
        return True

    async def import_contacts(self, rows: list[dict[str, str]]) -> tuple[int, int, list[str]]:
        created = 0
        skipped = 0
        errors: list[str] = []

        for row_number, raw in enumerate(rows, start=2):
            phone_number = (raw.get("phone_number") or raw.get("phone") or "").strip()
            if not phone_number:
                skipped += 1
                errors.append(f"Row {row_number}: phone_number is required")
                continue

            try:
                existing = await self.contact_repo.get_by_phone(phone_number)
                if existing:
                    skipped += 1
                    continue

                data = ContactCreate(
                    phone_number=phone_number,
                    email=raw.get("email") or None,
                    first_name=raw.get("first_name") or raw.get("first") or None,
                    last_name=raw.get("last_name") or raw.get("last") or None,
                    company=raw.get("company") or None,
                    timezone=raw.get("timezone") or None,
                    notes=raw.get("notes") or None,
                    status=raw.get("status") or "active",
                    do_not_call=(raw.get("do_not_call") or "").lower() in {"1", "true", "yes"},
                )
                await self.create_contact(data)
                created += 1
            except Exception as exc:
                skipped += 1
                errors.append(f"Row {row_number}: {exc}")

        return created, skipped, errors

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
