from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from apps.api.schemas.phone_number import PhoneNumberCreate, PhoneNumberUpdate, PhoneNumberResponse
from apps.api.schemas.common import PaginationParams, PaginatedResponse
from apps.api.repositories.phone_number_repo import PhoneNumberRepository
from apps.api.repositories.agent_repo import AgentRepository


class PhoneNumberService:
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = PhoneNumberRepository(session, tenant_id=tenant_id)
        self.agent_repo = AgentRepository(session, tenant_id=tenant_id)

    async def provision_number(self, data: PhoneNumberCreate) -> PhoneNumberResponse:
        existing = await self.repo.get_by_number(data.number)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number already registered"
            )

        if data.agent_id:
            agent = await self.agent_repo.get_by_id(data.agent_id)
            if not agent:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

        phone = await self.repo.create(**data.model_dump())
        await self.session.commit()
        return PhoneNumberResponse.model_validate(phone)

    async def list_numbers(
        self, pagination: PaginationParams
    ) -> PaginatedResponse[PhoneNumberResponse]:
        items, total = await self.repo.get_all(pagination)
        pages = (total + pagination.per_page - 1) // pagination.per_page if total > 0 else 0
        return PaginatedResponse(
            items=[PhoneNumberResponse.model_validate(i) for i in items],
            total=total,
            page=pagination.page,
            per_page=pagination.per_page,
            pages=pages,
        )

    async def get_number(self, phone_id: UUID) -> PhoneNumberResponse:
        phone = await self.repo.get_by_id(phone_id)
        if not phone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Phone number not found"
            )
        return PhoneNumberResponse.model_validate(phone)

    async def update_number(self, phone_id: UUID, data: PhoneNumberUpdate) -> PhoneNumberResponse:
        phone = await self.repo.get_by_id(phone_id)
        if not phone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Phone number not found"
            )

        update_data = data.model_dump(exclude_unset=True)
        if "agent_id" in update_data and update_data["agent_id"] is not None:
            agent = await self.agent_repo.get_by_id(update_data["agent_id"])
            if not agent:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

        updated = await self.repo.update(phone_id, **update_data)
        await self.session.commit()
        return PhoneNumberResponse.model_validate(updated)

    async def assign_to_agent(
        self, phone_id: UUID, agent_id: Optional[UUID]
    ) -> PhoneNumberResponse:
        phone = await self.repo.get_by_id(phone_id)
        if not phone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Phone number not found"
            )

        if agent_id:
            agent = await self.agent_repo.get_by_id(agent_id)
            if not agent:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

        updated = await self.repo.assign_agent(phone_id, agent_id)
        await self.session.commit()
        return PhoneNumberResponse.model_validate(updated)

    async def release_number(self, phone_id: UUID) -> None:
        phone = await self.repo.get_by_id(phone_id)
        if not phone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Phone number not found"
            )
        await self.repo.release_number(phone_id)
        await self.session.commit()
