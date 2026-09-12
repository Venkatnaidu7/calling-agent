from typing import Optional, Any
from pydantic import BaseModel, Field
import uuid
from datetime import datetime


# === Agent Schemas ===


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None


class AgentResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    status: str
    is_active: bool
    published_version_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class AgentVersionSummary(BaseModel):
    id: uuid.UUID
    version_number: int
    status: str
    name: str
    voice: str
    published_at: Optional[datetime]
    created_at: datetime
    model_config = {"from_attributes": True}


class AgentDetailResponse(AgentResponse):
    versions: list[AgentVersionSummary] = []


# === Agent Version Schemas ===


class AgentVersionCreate(BaseModel):
    """Create a new draft version of an agent."""

    name: str = Field(..., max_length=100)
    personality: Optional[str] = None
    voice: str = Field(default="ash", pattern="^(alloy|echo|shimmer|ash|ballad|coral|sage|verse)$")
    language: str = Field(default="en", max_length=10)
    languages: list[str] = ["en"]
    system_instructions: Optional[str] = None
    business_context: Optional[str] = None
    greeting_message: Optional[str] = None
    objectives: list[str] = []
    fallback_message: Optional[str] = None
    max_call_duration_seconds: int = Field(default=1800, ge=60, le=7200)
    knowledge_config: dict[str, Any] = {}
    tool_permissions: dict[str, Any] = {}
    transfer_rules: dict[str, Any] = {}
    business_hours: dict[str, Any] = {}
    compliance_config: dict[str, Any] = {}
    turn_detection_config: dict[str, Any] = {}
    loop_protection_config: dict[str, Any] = {}


class AgentVersionUpdate(BaseModel):
    """Update a draft version."""

    name: Optional[str] = Field(None, max_length=100)
    personality: Optional[str] = None
    voice: Optional[str] = Field(None, pattern="^(alloy|echo|shimmer|ash|ballad|coral|sage|verse)$")
    language: Optional[str] = None
    languages: Optional[list[str]] = None
    system_instructions: Optional[str] = None
    business_context: Optional[str] = None
    greeting_message: Optional[str] = None
    objectives: Optional[list[str]] = None
    fallback_message: Optional[str] = None
    max_call_duration_seconds: Optional[int] = Field(None, ge=60, le=7200)
    knowledge_config: Optional[dict[str, Any]] = None
    tool_permissions: Optional[dict[str, Any]] = None
    transfer_rules: Optional[dict[str, Any]] = None
    business_hours: Optional[dict[str, Any]] = None
    compliance_config: Optional[dict[str, Any]] = None
    turn_detection_config: Optional[dict[str, Any]] = None
    loop_protection_config: Optional[dict[str, Any]] = None


class AgentVersionResponse(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    version_number: int
    status: str
    name: str
    personality: Optional[str]
    voice: str
    language: str
    languages: list[str]
    system_instructions: Optional[str]
    business_context: Optional[str]
    greeting_message: Optional[str]
    objectives: list[str]
    fallback_message: Optional[str]
    max_call_duration_seconds: int
    knowledge_config: dict[str, Any]
    tool_permissions: dict[str, Any]
    transfer_rules: dict[str, Any]
    business_hours: dict[str, Any]
    compliance_config: dict[str, Any]
    turn_detection_config: dict[str, Any]
    loop_protection_config: dict[str, Any]
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


# === Publishing ===


class PublishAgentRequest(BaseModel):
    version_id: uuid.UUID


class TestAgentRequest(BaseModel):
    version_id: uuid.UUID
