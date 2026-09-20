from redis.asyncio import Redis
from fastapi import Request
from apps.api.config import settings

# Global redis connection
_redis_pool = None


async def init_redis():
    global _redis_pool
    if _redis_pool is None and settings.redis_url:
        _redis_pool = Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_pool


async def close_redis():
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.close()
        _redis_pool = None


def get_redis(request: Request) -> Redis | None:
    """Dependency to get Redis connection from app state"""
    return request.app.state.redis


# ─── Re-exports from middleware (all routers import from here) ───────────────
from apps.api.middleware.tenant import get_tenant_context  # noqa: E402, F401
from apps.api.middleware.auth import require_roles, require_permissions  # noqa: E402, F401

__all__ = [
    "init_redis",
    "close_redis",
    "get_redis",
    "get_tenant_context",
    "require_roles",
    "require_permissions",
]
