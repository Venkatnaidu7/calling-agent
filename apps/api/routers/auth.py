from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.schemas.auth import (
    RegisterRequest, LoginRequest, TokenResponse, RefreshTokenRequest,
    ChangePasswordRequest, ForgotPasswordRequest, ResetPasswordRequest,
)
from apps.api.schemas.user import CurrentUserResponse
from apps.api.services.auth_service import AuthService
from apps.api.database import get_db
from apps.api.middleware.auth import get_current_user
from apps.api.models import User
from apps.api.middleware.rate_limit import rate_limit

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(rate_limit(5, 3600))])
async def register(request: Request, data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    return await auth_service.register(data, ip=request.client.host, user_agent=request.headers.get("user-agent"))

@router.post("/login", response_model=TokenResponse, dependencies=[Depends(rate_limit(10, 60))])
async def login(request: Request, data: LoginRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    return await auth_service.login(data, ip=request.client.host, user_agent=request.headers.get("user-agent"))

@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: Request, data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    return await auth_service.refresh_token(data.refresh_token, ip=request.client.host, user_agent=request.headers.get("user-agent"))

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    await auth_service.logout(data.refresh_token, ip=request.client.host)

@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(request: Request, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    await auth_service.logout_all(current_user.id, ip=request.client.host)

@router.get("/me", response_model=CurrentUserResponse)
async def get_me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from apps.api.middleware.auth import ROLE_PERMISSIONS
    from apps.api.repositories.tenant_repo import TenantRepository

    tenant_repo = TenantRepository(db)
    tenant = await tenant_repo.get_by_id(current_user.tenant_id)
    permissions = ROLE_PERMISSIONS.get(current_user.role, [])

    user_data = {
        "id": current_user.id,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "role": current_user.role,
        "email_verified": current_user.email_verified,
        "is_active": current_user.is_active,
        "last_login_at": current_user.last_login_at,
        "created_at": current_user.created_at,
        "tenant": tenant,
        "permissions": permissions,
    }
    return CurrentUserResponse.model_validate(user_data)

@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    request: Request,
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from apps.api.utils.crypto import verify_password, hash_password
    from apps.api.services.audit_service import AuditService

    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    from apps.api.repositories.user_repo import UserRepository
    user_repo = UserRepository(db, tenant_id=current_user.tenant_id)
    await user_repo.update(current_user.id, password_hash=hash_password(data.new_password))

    audit_service = AuditService(db)
    await audit_service.log(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action="PASSWORD_CHANGED",
        resource_type="USER",
        resource_id=current_user.id,
        details={},
        ip=request.client.host,
    )
    await db.commit()
    return {"message": "Password changed successfully"}


@router.post("/forgot-password", status_code=status.HTTP_200_OK, dependencies=[Depends(rate_limit(5, 3600))])
async def forgot_password(request: Request, data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    Initiates password reset. Always returns success to prevent email enumeration.
    Generates a secure 15-minute token in Redis and dispatches an email.
    """
    import structlog
    from apps.api.repositories.user_repo import UserRepository
    from apps.api.utils.crypto import generate_secure_token, hash_token
    from apps.api.services.email_service import EmailService

    logger = structlog.get_logger()
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email_global(data.email)

    if user and user.is_active:
        raw_token = generate_secure_token(32)
        hashed = hash_token(raw_token)
        redis = request.app.state.redis
        if redis:
            await redis.set(f"pwd_reset:{hashed}", str(user.id), ex=900)
        
        email_service = EmailService()
        await email_service.send_password_reset_email(user.email, raw_token)
        logger.info("password_reset_initiated", email=data.email)

    return {"message": "If an account exists with that email, a password reset link has been sent."}


@router.post("/reset-password", status_code=status.HTTP_200_OK, dependencies=[Depends(rate_limit(5, 60))])
async def reset_password(request: Request, data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    Resets password using a validated one-time token from Redis.
    """
    import structlog
    import uuid
    from apps.api.repositories.user_repo import UserRepository
    from apps.api.repositories.session_repo import SessionRepository
    from apps.api.utils.crypto import hash_token, hash_password

    logger = structlog.get_logger()
    redis = request.app.state.redis
    if not redis:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Password reset service temporarily unavailable.",
        )

    hashed = hash_token(data.token)
    redis_key = f"pwd_reset:{hashed}"
    user_id_str = await redis.get(redis_key)

    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token.",
        )

    if isinstance(user_id_str, bytes):
        user_id_str = user_id_str.decode("utf-8")

    user_uuid = uuid.UUID(user_id_str)
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_uuid)

    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found or inactive.")

    # Update password
    new_hash = hash_password(data.new_password)
    await user_repo.update(user.id, password_hash=new_hash)

    # Invalidate all active login sessions
    session_repo = SessionRepository(db)
    await session_repo.revoke_all_for_user(user.id)

    # Delete token from Redis to prevent replay
    await redis.delete(redis_key)
    await db.commit()

    logger.info("password_reset_completed", user_id=str(user.id))
    return {"message": "Password has been reset successfully. You can now log in with your new password."}
