import asyncio
import uuid
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

from apps.api.database import Base, get_db
from apps.api.main import create_app
from apps.api.config import settings
from apps.api.utils.crypto import hash_password, create_access_token
from apps.api.models import Tenant, User
from datetime import timedelta

# Use a test database
db_url_str = str(settings.database_url)
if db_url_str.endswith("_test"):
    TEST_DATABASE_URL = db_url_str
else:
    TEST_DATABASE_URL = db_url_str.replace("/ai_voice_platform", "/ai_voice_platform_test")

# Create test engine
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, pool_pre_ping=True)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create tables, yield session, drop tables after test."""
    async with test_engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def app(db_session: AsyncSession):
    """Create app with test DB override."""
    test_app = create_app()

    async def override_get_db():
        yield db_session

    test_app.dependency_overrides[get_db] = override_get_db
    # Set dummy redis to skip rate limiting
    test_app.state.redis = None
    yield test_app
    test_app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """HTTP test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def tenant_a(db_session: AsyncSession) -> Tenant:
    """Create Tenant A for isolation tests."""
    tenant = Tenant(
        id=uuid.uuid4(),
        name="Tenant A",
        slug="tenant-a",
        business_name="Business A",
        country="US",
        timezone="America/New_York",
        status="active",
    )
    db_session.add(tenant)
    await db_session.flush()
    return tenant


@pytest_asyncio.fixture
async def tenant_b(db_session: AsyncSession) -> Tenant:
    """Create Tenant B for isolation tests."""
    tenant = Tenant(
        id=uuid.uuid4(),
        name="Tenant B",
        slug="tenant-b",
        business_name="Business B",
        country="IN",
        timezone="Asia/Kolkata",
        status="active",
    )
    db_session.add(tenant)
    await db_session.flush()
    return tenant


@pytest_asyncio.fixture
async def user_a(db_session: AsyncSession, tenant_a: Tenant) -> User:
    """Create owner user for Tenant A."""
    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        email="owner@tenant-a.com",
        password_hash=hash_password("Password1"),
        first_name="Alice",
        last_name="Admin",
        role="TENANT_OWNER",
        is_active=True,
        email_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def user_b(db_session: AsyncSession, tenant_b: Tenant) -> User:
    """Create owner user for Tenant B."""
    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant_b.id,
        email="owner@tenant-b.com",
        password_hash=hash_password("Password1"),
        first_name="Bob",
        last_name="Boss",
        role="TENANT_OWNER",
        is_active=True,
        email_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


def make_token(user: User) -> str:
    """Generate a JWT access token for a user."""
    return create_access_token(
        data={"sub": str(user.id), "tenant_id": str(user.tenant_id), "role": user.role},
        expires_delta=timedelta(hours=1),
    )


def auth_headers(user: User) -> dict:
    """Generate Authorization header for a user."""
    return {"Authorization": f"Bearer {make_token(user)}"}
