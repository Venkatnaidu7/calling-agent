import pytest
import uuid
from httpx import AsyncClient
from apps.api.models import User, Tenant, PhoneNumber, CallLog
from tests.conftest import auth_headers


class TestCallInfrastructure:
    @pytest.mark.asyncio
    async def test_provision_phone_number(self, client: AsyncClient, user_a: User):
        response = await client.post(
            "/api/v1/phone-numbers",
            headers=auth_headers(user_a),
            json={
                "number": "+14155552671",
                "friendly_name": "Main Support Line",
                "capabilities": {"voice": True, "sms": True},
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["number"] == "+14155552671"
        assert data["status"] == "active"

    @pytest.mark.asyncio
    async def test_list_calls_empty(self, client: AsyncClient, user_a: User):
        response = await client.get("/api/v1/calls", headers=auth_headers(user_a))
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_call_stats(self, client: AsyncClient, user_a: User):
        response = await client.get("/api/v1/calls/stats", headers=auth_headers(user_a))
        assert response.status_code == 200
        data = response.json()
        assert "total_calls" in data
        assert "by_status" in data
