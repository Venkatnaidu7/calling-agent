import pytest
import pytest_asyncio
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.conftest import auth_headers
from apps.api.models import User, Tenant
from apps.api.utils.crypto import hash_password

@pytest_asyncio.fixture
async def analyst_user(db_session: AsyncSession, tenant_a: Tenant) -> User:
    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        email="analyst@tenant-a.com",
        password_hash=hash_password("Password1"),
        first_name="Ana",
        last_name="Lyst",
        role="ANALYST",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user

@pytest_asyncio.fixture
async def readonly_user(db_session: AsyncSession, tenant_a: Tenant) -> User:
    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        email="readonly@tenant-a.com",
        password_hash=hash_password("Password1"),
        first_name="Read",
        last_name="Only",
        role="READ_ONLY",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user

class TestRoleAuthorization:
    @pytest.mark.asyncio
    async def test_owner_can_create_user(self, client: AsyncClient, user_a: User):
        response = await client.post("/api/v1/users", 
            headers=auth_headers(user_a),
            json={"email": "new@tenant-a.com", "password": "SecurePass1", "first_name": "New", "role": "ANALYST"}
        )
        assert response.status_code == 201
    
    @pytest.mark.asyncio
    async def test_analyst_cannot_create_user(self, client: AsyncClient, analyst_user: User):
        response = await client.post("/api/v1/users",
            headers=auth_headers(analyst_user),
            json={"email": "hack@tenant-a.com", "password": "SecurePass1", "first_name": "Hack", "role": "ANALYST"}
        )
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_readonly_cannot_create_user(self, client: AsyncClient, readonly_user: User):
        response = await client.post("/api/v1/users",
            headers=auth_headers(readonly_user),
            json={"email": "hack@tenant-a.com", "password": "SecurePass1", "first_name": "Hack", "role": "READ_ONLY"}
        )
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_readonly_can_list_users(self, client: AsyncClient, readonly_user: User):
        response = await client.get("/api/v1/users", headers=auth_headers(readonly_user))
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_analyst_cannot_delete_user(self, client: AsyncClient, analyst_user: User, user_a: User):
        response = await client.delete(f"/api/v1/users/{user_a.id}", headers=auth_headers(analyst_user))
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_access(self, client: AsyncClient):
        response = await client.get("/api/v1/users")
        assert response.status_code == 401
