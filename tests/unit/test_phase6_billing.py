import pytest
from httpx import AsyncClient
from apps.api.models import User
from tests.conftest import auth_headers


class TestBillingAndAnalytics:
    @pytest.mark.asyncio
    async def test_get_plans(self, client: AsyncClient):
        response = await client.get("/api/v1/billing/plans")
        assert response.status_code == 200
        data = response.json()
        assert "starter" in data
        assert "pro" in data
        assert "enterprise" in data

    @pytest.mark.asyncio
    async def test_get_subscription(self, client: AsyncClient, user_a: User):
        response = await client.get("/api/v1/billing/subscription", headers=auth_headers(user_a))
        assert response.status_code == 200
        data = response.json()
        assert "plan_tier" in data
        assert "monthly_minute_limit" in data

    @pytest.mark.asyncio
    async def test_get_analytics_dashboard(self, client: AsyncClient, user_a: User):
        response = await client.get("/api/v1/analytics/dashboard", headers=auth_headers(user_a))
        assert response.status_code == 200
        data = response.json()
        assert "overview" in data
        assert "sentiment" in data
        assert "daily_volume" in data
