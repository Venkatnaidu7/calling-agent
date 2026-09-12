from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from apps.api.database import get_db

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}


@router.get("/liveness")
async def liveness():
    return {"status": "alive"}


@router.get("/readiness")
async def readiness(request: Request, db: AsyncSession = Depends(get_db)):
    checks = {"database": "down", "redis": "down"}
    status_code = 200

    # Check DB
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "up"
    except Exception:
        status_code = 503

    # Check Redis
    try:
        redis = request.app.state.redis
        if redis and await redis.ping():
            checks["redis"] = "up"
    except Exception:
        status_code = 503

    status_msg = "ready" if status_code == 200 else "unready"
    return {"status": status_msg, "checks": checks}
