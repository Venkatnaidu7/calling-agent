import uuid
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class PlanTier(BaseModel):
    id: str
    name: str
    price_monthly_dollars: int
    monthly_minutes: int
    concurrency_limit: int
    features: List[str]


class SubscriptionResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    plan_tier: str
    status: str
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool
    trial_ends_at: Optional[datetime] = None
    monthly_minute_limit: int
    concurrency_limit: int
    minutes_used_this_period: int = 0

    model_config = {"from_attributes": True}


class CreateCheckoutSessionRequest(BaseModel):
    plan_tier: str = Field(..., pattern="^(starter|pro|enterprise)$")
    success_url: str
    cancel_url: str


class CheckoutSessionResponse(BaseModel):
    checkout_url: str
    session_id: str


class CustomerPortalResponse(BaseModel):
    portal_url: str


class UsageSummaryResponse(BaseModel):
    tenant_id: uuid.UUID
    period_start: datetime
    period_end: datetime
    total_minutes_used: int
    minute_limit: int
    total_cost_cents: int
    by_metric: Dict[str, int]
