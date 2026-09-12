import time
from typing import Callable
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from redis.asyncio import Redis


class RateLimiter:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def is_allowed(self, key: str, limit: int, window_seconds: int) -> bool:

        current_time = time.time()
        window_start = current_time - window_seconds

        pipeline = self.redis.pipeline()
        # Remove old requests
        pipeline.zremrangebyscore(key, 0, window_start)
        # Add current request
        pipeline.zadd(key, {str(current_time): current_time})
        # Count requests in window
        pipeline.zcard(key)
        # Set expiry on the key to cleanup
        pipeline.expire(key, window_seconds)

        results = await pipeline.execute()
        request_count = results[2]

        return request_count <= limit


def rate_limit(limit: int, window_seconds: int = 60) -> Callable:
    async def dependency(request: Request):
        redis = request.app.state.redis
        if not redis:
            return  # Skip if redis not configured

        identifier = request.client.host
        if hasattr(request.state, "user_id"):
            identifier = str(request.state.user_id)

        endpoint = request.url.path
        key = f"rate_limit:{identifier}:{endpoint}"

        limiter = RateLimiter(redis)
        is_allowed = await limiter.is_allowed(key, limit, window_seconds)

        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(window_seconds)},
            )

    return dependency


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/v1/voice/stream") or request.url.path == "/health":
            return await call_next(request)

        redis = getattr(request.app.state, "redis", None)
        if redis:
            client_ip = request.client.host if request.client else "unknown"
            key = f"rate_limit:global:{client_ip}"
            limiter = RateLimiter(redis)
            if not await limiter.is_allowed(key, limit=300, window_seconds=60):
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "success": False,
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": "Too many requests. Please try again later.",
                        },
                    },
                    headers={"Retry-After": "60"},
                )
        return await call_next(request)
