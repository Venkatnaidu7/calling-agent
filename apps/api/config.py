from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Application
    app_env: str = Field(default="development")
    app_version: str = Field(default="0.1.0")
    app_secret_key: str = Field(default="change-me-in-production-use-a-64-char-random-string")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    app_debug: bool = Field(default=False)
    app_log_level: str = Field(default="INFO")

    # Database
    database_url: str = Field(...)  # Required: Must be provided via env
    database_pool_size: int = Field(default=20)
    database_max_overflow: int = Field(default=10)

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")
    celery_broker_url: str = Field(default="redis://localhost:6379/1")
    celery_result_backend: str = Field(default="redis://localhost:6379/2")

    # JWT
    jwt_secret_key: str = Field(default="change-me-in-production-use-a-64-char-random-string")
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=30)
    jwt_refresh_token_expire_days: int = Field(default=7)

    # OpenAI
    openai_api_key: str = Field(default="")
    openai_realtime_model: str = Field(default="gpt-4o-mini-realtime-preview")
    openai_chat_model: str = Field(default="gpt-4o-mini")
    openai_embedding_model: str = Field(default="text-embedding-3-small")

    # Twilio
    twilio_account_sid: str = Field(default="")
    twilio_auth_token: str = Field(default="")
    twilio_webhook_base_url: str = Field(default="")

    # Plivo
    plivo_auth_id: str = Field(default="")
    plivo_auth_token: str = Field(default="")

    # Stripe
    stripe_secret_key: str = Field(default="")
    stripe_webhook_secret: str = Field(default="")
    stripe_publishable_key: str = Field(default="")

    # S3
    s3_endpoint_url: str = Field(default="")
    s3_access_key_id: str = Field(default="")
    s3_secret_access_key: str = Field(default="")
    s3_bucket_name: str = Field(default="ai-voice-platform")
    s3_region: str = Field(default="us-east-1")

    # CORS
    cors_allowed_origins: str = Field(default="http://localhost:3000")

    # Rate Limiting
    rate_limit_login: str = Field(default="5/minute")
    rate_limit_api: str = Field(default="100/minute")
    rate_limit_upload: str = Field(default="10/minute")

    # Call Limits
    call_max_duration_seconds: int = Field(default=3600)
    call_max_concurrent_per_tenant: int = Field(default=10)

    # Email
    sendgrid_api_key: str = Field(default="")
    email_from_address: str = Field(default="noreply@example.com")
    email_from_name: str = Field(default="AI Voice Platform")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()
