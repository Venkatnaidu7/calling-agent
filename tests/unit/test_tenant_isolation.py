import pytest
import uuid
from httpx import AsyncClient
from tests.conftest import auth_headers
from apps.api.models import User, Tenant
from apps.api.utils.crypto import hash_password

class TestTenantIsolation:
    """Prove that cross-tenant access is impossible. Required by spec §7."""
    
    @pytest.mark.asyncio
    async def test_tenant_a_cannot_list_tenant_b_users(self, client: AsyncClient, user_a: User, user_b: User):
        """Tenant A listing users should NOT see Tenant B users."""
        response = await client.get("/api/v1/users", headers=auth_headers(user_a))
        assert response.status_code == 200
        data = response.json()
        user_emails = [u["email"] for u in data["items"]]
        # Should see Tenant A's user
        assert "owner@tenant-a.com" in user_emails
        # Should NOT see Tenant B's user
        assert "owner@tenant-b.com" not in user_emails
    
    @pytest.mark.asyncio
    async def test_tenant_a_cannot_read_tenant_b_user(self, client: AsyncClient, user_a: User, user_b: User):
        """Tenant A cannot directly access a Tenant B user by ID."""
        response = await client.get(f"/api/v1/users/{user_b.id}", headers=auth_headers(user_a))
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_tenant_b_cannot_list_tenant_a_users(self, client: AsyncClient, user_a: User, user_b: User):
        response = await client.get("/api/v1/users", headers=auth_headers(user_b))
        data = response.json()
        user_emails = [u["email"] for u in data["items"]]
        assert "owner@tenant-b.com" in user_emails
        assert "owner@tenant-a.com" not in user_emails
    
    @pytest.mark.asyncio
    async def test_tenant_a_cannot_modify_tenant_b_user(self, client: AsyncClient, user_a: User, user_b: User):
        """Tenant A cannot update a Tenant B user."""
        response = await client.put(
            f"/api/v1/users/{user_b.id}",
            headers=auth_headers(user_a),
            json={"first_name": "Hacked"}
        )
        assert response.status_code in [404, 403]
    
    @pytest.mark.asyncio
    async def test_tenant_a_cannot_delete_tenant_b_user(self, client: AsyncClient, user_a: User, user_b: User):
        """Tenant A cannot deactivate a Tenant B user."""
        response = await client.delete(f"/api/v1/users/{user_b.id}", headers=auth_headers(user_a))
        assert response.status_code in [404, 403]
    
    @pytest.mark.asyncio
    async def test_cross_tenant_user_count(self, client: AsyncClient, user_a: User, user_b: User):
        """Each tenant should only see their own user count."""
        resp_a = await client.get("/api/v1/users", headers=auth_headers(user_a))
        resp_b = await client.get("/api/v1/users", headers=auth_headers(user_b))
        # Each tenant has exactly 1 user (the owner)
        assert resp_a.json()["total"] == 1
        assert resp_b.json()["total"] == 1
