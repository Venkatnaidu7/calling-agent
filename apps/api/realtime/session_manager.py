import json
import uuid
from datetime import datetime, timezone
from redis.asyncio import Redis
import structlog

logger = structlog.get_logger()

SESSION_PREFIX = "call_session:"
SESSION_TTL = 7200  # 2 hours max


class CallSession:
    """Represents the state of an active voice call."""

    def __init__(
        self,
        call_id: str,
        tenant_id: str,
        agent_id: str,
        agent_version_id: str,
        direction: str,  # 'inbound' or 'outbound'
        from_number: str,
        to_number: str,
        provider_call_id: str = "",
        stream_sid: str = "",
        language: str = "en",
        state: str = "connecting",
        start_time: str = "",
        last_activity: str = "",
        current_assistant_item_id: str = "",
        played_audio_ms: int = 0,
        tool_calls_count: int = 0,
        transfer_status: str = "",
        metadata: dict = None,
    ):
        self.call_id = call_id
        self.tenant_id = tenant_id
        self.agent_id = agent_id
        self.agent_version_id = agent_version_id
        self.direction = direction
        self.from_number = from_number
        self.to_number = to_number
        self.provider_call_id = provider_call_id
        self.stream_sid = stream_sid
        self.language = language
        self.state = state
        self.start_time = start_time or datetime.now(timezone.utc).isoformat()
        self.last_activity = last_activity or datetime.now(timezone.utc).isoformat()
        self.current_assistant_item_id = current_assistant_item_id
        self.played_audio_ms = played_audio_ms
        self.tool_calls_count = tool_calls_count
        self.transfer_status = transfer_status
        self.metadata = metadata or {}

    def to_dict(self) -> dict:
        return {
            "call_id": self.call_id,
            "tenant_id": self.tenant_id,
            "agent_id": self.agent_id,
            "agent_version_id": self.agent_version_id,
            "direction": self.direction,
            "from_number": self.from_number,
            "to_number": self.to_number,
            "provider_call_id": self.provider_call_id,
            "stream_sid": self.stream_sid,
            "language": self.language,
            "state": self.state,
            "start_time": self.start_time,
            "last_activity": self.last_activity,
            "current_assistant_item_id": self.current_assistant_item_id,
            "played_audio_ms": str(self.played_audio_ms),
            "tool_calls_count": str(self.tool_calls_count),
            "transfer_status": self.transfer_status,
            "metadata": json.dumps(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CallSession":
        data["played_audio_ms"] = int(data.get("played_audio_ms", 0))
        data["tool_calls_count"] = int(data.get("tool_calls_count", 0))
        md = data.get("metadata", "{}")
        data["metadata"] = json.loads(md) if isinstance(md, str) else md
        return cls(**data)


class SessionManager:
    """Manages call session state in Redis."""

    def __init__(self, redis: Redis):
        self.redis = redis

    async def create_session(self, session: CallSession) -> None:
        key = f"{SESSION_PREFIX}{session.call_id}"
        await self.redis.hset(key, mapping=session.to_dict())
        await self.redis.expire(key, SESSION_TTL)

        # Maintain tenant-specific active session set
        tenant_set_key = f"tenant_sessions:{session.tenant_id}"
        await self.redis.sadd(tenant_set_key, session.call_id)
        await self.redis.expire(tenant_set_key, SESSION_TTL)

        logger.info("session_created", call_id=session.call_id, tenant_id=session.tenant_id)

    async def create_pending_session(self, call_id: str, tenant_id: uuid.UUID) -> None:
        """Store the tenant_id for a call_id before the WebSocket connects."""
        key = f"pending_session:{call_id}"
        await self.redis.set(key, str(tenant_id), ex=300)  # 5 min TTL
        logger.info("pending_session_created", call_id=call_id, tenant_id=str(tenant_id))

    async def get_pending_tenant(self, call_id: str) -> str | None:
        """Retrieve the tenant_id for a pending call."""
        key = f"pending_session:{call_id}"
        val = await self.redis.get(key)
        if not val:
            return None
        return val.decode("utf-8") if isinstance(val, bytes) else str(val)

    async def delete_pending_session(self, call_id: str) -> None:
        await self.redis.delete(f"pending_session:{call_id}")

    async def get_session(self, call_id: str) -> CallSession | None:
        key = f"{SESSION_PREFIX}{call_id}"
        data = await self.redis.hgetall(key)
        if not data:
            return None
        return CallSession.from_dict(data)

    async def update_session(self, call_id: str, **kwargs) -> None:
        key = f"{SESSION_PREFIX}{call_id}"
        kwargs["last_activity"] = datetime.now(timezone.utc).isoformat()
        # Handle metadata serialization
        if "metadata" in kwargs and isinstance(kwargs["metadata"], dict):
            kwargs["metadata"] = json.dumps(kwargs["metadata"])
        # Convert ints to strings for Redis
        for k, v in kwargs.items():
            if isinstance(v, int):
                kwargs[k] = str(v)
        await self.redis.hset(key, mapping=kwargs)

    async def delete_session(self, call_id: str, tenant_id: str | None = None) -> None:
        key = f"{SESSION_PREFIX}{call_id}"

        # Remove from tenant set if tenant_id is provided
        if tenant_id:
            tenant_set_key = f"tenant_sessions:{tenant_id}"
            await self.redis.srem(tenant_set_key, call_id)

        await self.redis.delete(key)
        logger.info("session_deleted", call_id=call_id)

    async def get_active_sessions_count(self, tenant_id: str) -> int:
        tenant_set_key = f"tenant_sessions:{tenant_id}"
        count = await self.redis.scard(tenant_set_key)
        return count if count else 0
