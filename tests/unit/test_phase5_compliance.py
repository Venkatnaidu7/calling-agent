import pytest
from httpx import AsyncClient
from apps.api.models import User
from tests.conftest import auth_headers


class TestComplianceAndDNC:
    @pytest.mark.asyncio
    async def test_add_to_dnc(self, client: AsyncClient, user_a: User):
        response = await client.post(
            "/api/v1/compliance/dnc",
            headers=auth_headers(user_a),
            json={
                "phone_number": "+15551234567",
                "source": "manual",
                "reason": "Requested opt out",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["phone_number"] == "+15551234567"
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_compliance_check_dnc_blocked(self, client: AsyncClient, user_a: User):
        # First ensure it is added to DNC
        await client.post(
            "/api/v1/compliance/dnc",
            headers=auth_headers(user_a),
            json={
                "phone_number": "+15559876543",
                "source": "manual",
                "reason": "Opt-out",
            },
        )

        # Check if can call
        response = await client.get(
            "/api/v1/compliance/check?phone_number=%2B15559876543",
            headers=auth_headers(user_a),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] is False
        assert "DNC" in str(data.get("reasons", []))
