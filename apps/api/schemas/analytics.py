import uuid
from typing import List
from pydantic import BaseModel


class OverviewMetrics(BaseModel):
    total_calls: int
    completed_calls: int
    failed_calls: int
    completion_rate_percent: float
    total_duration_minutes: float
    avg_duration_seconds: float
    estimated_cost_dollars: float


class SentimentBreakdown(BaseModel):
    positive: int
    neutral: int
    negative: int
    unknown: int


class AgentPerformanceMetrics(BaseModel):
    agent_id: uuid.UUID
    agent_name: str
    total_calls: int
    avg_duration_seconds: float
    positive_sentiment_percent: float
    tool_calls_count: int


class DailyCallVolume(BaseModel):
    date: str
    inbound_count: int
    outbound_count: int
    total_minutes: float


class AnalyticsDashboardResponse(BaseModel):
    overview: OverviewMetrics
    sentiment: SentimentBreakdown
    daily_volume: List[DailyCallVolume]
    agent_performance: List[AgentPerformanceMetrics]
