import pytest
from httpx import AsyncClient
from apps.api.utils.crypto import (
    hash_password,
    verify_password,
    create_access_token,
    verify_access_token,
)


# Test password hashing
class TestPasswordHashing:
    def test_hash_and_verify(self):
        password = "SecurePass1"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed)

    def test_wrong_password(self):
        hashed = hash_password("CorrectPass1")
        assert not verify_password("WrongPass1", hashed)

    def test_different_hashes(self):
        """Same password should produce different hashes (salt)."""
        h1 = hash_password("SamePass1")
        h2 = hash_password("SamePass1")
        assert h1 != h2


# Test JWT tokens
class TestJWTTokens:
    def test_create_and_verify(self):
        data = {"sub": "user-123", "tenant_id": "tenant-456", "role": "TENANT_OWNER"}
        token = create_access_token(data)
        payload = verify_access_token(token)
        assert payload["sub"] == "user-123"
        assert payload["tenant_id"] == "tenant-456"

    def test_invalid_token(self):
        with pytest.raises(ValueError):
            verify_access_token("invalid-token")

    def test_token_contains_expiry(self):
        token = create_access_token({"sub": "test"})
        payload = verify_access_token(token)
        assert "exp" in payload


# Test registration API
class TestRegistration:
    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass1",
                "first_name": "John",
                "last_name": "Doe",
                "business_name": "Test Business",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "dup@example.com",
                "password": "SecurePass1",
                "business_name": "Biz 1",
            },
        )
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "dup@example.com",
                "password": "SecurePass1",
                "business_name": "Biz 2",
            },
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "weak@example.com",
                "password": "weak",
                "business_name": "Biz",
            },
        )
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_register_no_uppercase(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "weak@example.com",
                "password": "nouppercase1",
                "business_name": "Biz",
            },
        )
        assert response.status_code == 422


# Test login API
class TestLogin:
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        # Register first
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "login@example.com",
                "password": "SecurePass1",
                "business_name": "Login Biz",
            },
        )
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "login@example.com",
                "password": "SecurePass1",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "login2@example.com",
                "password": "SecurePass1",
                "business_name": "Biz",
            },
        )
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "login2@example.com",
                "password": "WrongPass1",
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nobody@example.com",
                "password": "Anything1",
            },
        )
        assert response.status_code == 401


# Test /me endpoint
class TestCurrentUser:
    @pytest.mark.asyncio
    async def test_me_authenticated(self, client: AsyncClient):
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "me@example.com",
                "password": "SecurePass1",
                "business_name": "My Biz",
            },
        )
        token = reg.json()["access_token"]
        response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@example.com"
        assert data["role"] == "TENANT_OWNER"

    @pytest.mark.asyncio
    async def test_me_unauthenticated(self, client: AsyncClient):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401


# Test token refresh
class TestRefreshToken:
    @pytest.mark.asyncio
    async def test_refresh_success(self, client: AsyncClient):
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "refresh@example.com",
                "password": "SecurePass1",
                "business_name": "Refresh Biz",
            },
        )
        refresh_token = reg.json()["refresh_token"]
        response = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        # New refresh token should be different
        assert data["refresh_token"] != refresh_token

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/refresh", json={"refresh_token": "invalid"})
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_reuse_revoked(self, client: AsyncClient):
        """Using a refresh token that was already rotated should fail."""
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "reuse@example.com",
                "password": "SecurePass1",
                "business_name": "Reuse Biz",
            },
        )
        old_refresh = reg.json()["refresh_token"]
        # Use it once (rotates)
        await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
        # Try to use old one again
        response = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
        assert response.status_code == 401
