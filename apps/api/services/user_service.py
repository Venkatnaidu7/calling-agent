from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from apps.api.schemas.user import UserCreate, UserUpdate, UserResponse
from apps.api.schemas.common import PaginationParams, PaginatedResponse
from apps.api.repositories.user_repo import UserRepository
from apps.api.utils.crypto import hash_password


class UserService:
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.user_repo = UserRepository(session, tenant_id=tenant_id)

    async def create_user(self, data: UserCreate) -> UserResponse:
        existing_user = await self.user_repo.get_by_email_global(data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already taken"
            )

        dumped_data = data.model_dump()
        if "password" in dumped_data:
            dumped_data["password_hash"] = hash_password(dumped_data.pop("password"))

        user = await self.user_repo.create(**dumped_data)
        await self.session.commit()
        return UserResponse.model_validate(user)

    async def get_user(self, user_id: UUID) -> UserResponse:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return UserResponse.model_validate(user)

    async def update_user(self, user_id: UUID, data: UserUpdate) -> UserResponse:
        dumped_data = data.model_dump(exclude_unset=True)
        if "password" in dumped_data:
            dumped_data["password_hash"] = hash_password(dumped_data.pop("password"))

        user = await self.user_repo.update(user_id, **dumped_data)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        await self.session.commit()
        return UserResponse.model_validate(user)

    async def list_users(self, pagination: PaginationParams) -> PaginatedResponse[UserResponse]:
        items, total = await self.user_repo.list_by_tenant(pagination)
        pages = (total + pagination.per_page - 1) // pagination.per_page if total > 0 else 0
        return PaginatedResponse(
            items=[UserResponse.model_validate(i) for i in items],
            total=total,
            page=pagination.page,
            per_page=pagination.per_page,
            pages=pages,
        )

    async def change_role(self, user_id: UUID, new_role: str) -> UserResponse:
        user = await self.user_repo.update(user_id, role=new_role)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        await self.session.commit()
        return UserResponse.model_validate(user)

    async def deactivate_user(self, user_id: UUID) -> None:
        user = await self.user_repo.update(user_id, is_active=False)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        await self.session.commit()
