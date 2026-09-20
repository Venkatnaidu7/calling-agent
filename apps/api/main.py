from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
from apps.api.config import settings
from apps.api.middleware.request_id import RequestIDMiddleware
from apps.api.middleware.security_headers import SecurityHeadersMiddleware
from apps.api.middleware.rate_limit import RateLimitMiddleware
from apps.api.routers import health, auth, tenants, users, agents, voice, knowledge
from apps.api.dependencies import init_redis, close_redis

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up application...")
    app.state.redis = await init_redis()
    yield
    # Shutdown
    logger.info("Shutting down application...")
    await close_redis()


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Voice Calling SaaS Platform",
        description="Phase 1 Foundation API",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # Middleware setup (order matters)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception Handlers
    from fastapi.exceptions import RequestValidationError
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        if request.url.path.startswith("/api/v1/auth/login") or request.url.path.startswith("/api/v1/auth/register"):
            logger.warning("auth_validation_failed", errors=exc.errors(), path=request.url.path)
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid input provided."}
            )
        # Default behavior for other routes
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()}
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception", exc_info=exc, path=request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred.",
                },
            },
        )

    # Routers
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(tenants.router)
    app.include_router(users.router)
    app.include_router(agents.router)
    app.include_router(voice.router)
    app.include_router(knowledge.router, prefix="/api/v1")

    from apps.api.routers import (
        contacts,
        campaigns,
        compliance,
        phone_numbers,
        call_logs,
        billing,
        analytics,
        webhooks,
    )

    app.include_router(contacts.router)
    app.include_router(campaigns.router)
    app.include_router(compliance.router)
    app.include_router(phone_numbers.router)
    app.include_router(call_logs.router)
    app.include_router(billing.router)
    app.include_router(analytics.router)
    app.include_router(webhooks.router)

    # Prometheus metrics
    try:
        from prometheus_fastapi_instrumentator import Instrumentator
        Instrumentator().instrument(app).expose(app)
    except ImportError:
        logger.warning("prometheus_fastapi_instrumentator not installed, /metrics endpoint unavailable")

    return app


app = create_app()
