from datetime import datetime, timezone, timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from apps.api.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from apps.api.repositories.user_repo import UserRepository
from apps.api.repositories.tenant_repo import TenantRepository
from apps.api.repositories.session_repo import SessionRepository
from apps.api.services.audit_service import AuditService
from apps.api.utils.crypto import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    hash_token,
)
from apps.api.config import settings


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.tenant_repo = TenantRepository(session)
        self.session_repo = SessionRepository(session)
        self.audit_service = AuditService(session)

    async def register(
        self, data: RegisterRequest, ip: str = None, user_agent: str = None
    ) -> TokenResponse:
        existing_user = await self.user_repo.get_by_email_global(data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
            )

        # Create tenant
        tenant = await self.tenant_repo.create(
            name=data.business_name, business_name=data.business_name
        )

        # Create user
        hashed_password = hash_password(data.password)
        user = await self.user_repo.create(
            tenant_id=tenant.id,
            email=data.email,
            password_hash=hashed_password,
            first_name=data.first_name,
            last_name=data.last_name,
            role="TENANT_OWNER",
            is_active=True,
            email_verified=False,
        )

        # Generate tokens
        access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": str(user.id), "tenant_id": str(tenant.id), "role": user.role},
            expires_delta=access_token_expires,
        )

        raw_refresh, hashed_refresh = create_refresh_token()
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.jwt_refresh_token_expire_days
        )

        # Create session
        await self.session_repo.create(
            user_id=user.id,
            tenant_id=tenant.id,
            refresh_token_hash=hashed_refresh,
            expires_at=expires_at,
            ip_address=ip,
            user_agent=user_agent,
        )

        # Audit log
        await self.audit_service.log(
            tenant_id=tenant.id,
            user_id=user.id,
            action="USER_REGISTER",
            resource_type="USER",
            resource_id=user.id,
            details={"email": user.email},
            ip=ip,
        )

        await self.session.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )

    async def login(
        self, data: LoginRequest, ip: str = None, user_agent: str = None
    ) -> TokenResponse:
        user = await self.user_repo.get_by_email_global(data.email)
        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive"
            )

        tenant = await self.tenant_repo.get_by_id(user.tenant_id)
        if not tenant or tenant.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Tenant account is not active"
            )

        # Update last login
        await self.user_repo.update(user.id, last_login_at=datetime.now(timezone.utc))

        # Generate tokens
        access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": str(user.id), "tenant_id": str(tenant.id), "role": user.role},
            expires_delta=access_token_expires,
        )

        raw_refresh, hashed_refresh = create_refresh_token()
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.jwt_refresh_token_expire_days
        )

        # Create session
        await self.session_repo.create(
            user_id=user.id,
            tenant_id=tenant.id,
            refresh_token_hash=hashed_refresh,
            expires_at=expires_at,
            ip_address=ip,
            user_agent=user_agent,
        )

        # Audit log
        await self.audit_service.log(
            tenant_id=tenant.id,
            user_id=user.id,
            action="USER_LOGIN",
            resource_type="USER",
            resource_id=user.id,
            details={"email": user.email},
            ip=ip,
        )

        await self.session.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )

    async def refresh_token(
        self, token: str, ip: str = None, user_agent: str = None
    ) -> TokenResponse:
        hashed_token = hash_token(token)
        user_session = await self.session_repo.get_by_refresh_token_hash(hashed_token)

        if not user_session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        if user_session.revoked_at or user_session.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired or revoked"
            )

        user = await self.user_repo.get_by_id(user_session.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive"
            )

        # Revoke old session
        await self.session_repo.revoke(user_session.id)

        # Generate new tokens
        access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": str(user.id), "tenant_id": str(user.tenant_id), "role": user.role},
            expires_delta=access_token_expires,
        )

        raw_refresh, hashed_refresh = create_refresh_token()
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.jwt_refresh_token_expire_days
        )

        # Create new session
        await self.session_repo.create(
            user_id=user.id,
            tenant_id=user.tenant_id,
            refresh_token_hash=hashed_refresh,
            expires_at=expires_at,
            ip_address=ip or user_session.ip_address,
            user_agent=user_agent or user_session.user_agent,
        )

        await self.session.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )

    async def logout(self, refresh_token: str, ip: str = None) -> None:
        hashed_token = hash_token(refresh_token)
        user_session = await self.session_repo.get_by_refresh_token_hash(hashed_token)

        if user_session and not user_session.revoked_at:
            await self.session_repo.revoke(user_session.id)
            await self.audit_service.log(
                tenant_id=user_session.tenant_id,
                user_id=user_session.user_id,
                action="USER_LOGOUT",
                resource_type="SESSION",
                resource_id=user_session.id,
                details={},
                ip=ip,
            )
            await self.session.commit()

    async def logout_all(self, user_id: UUID, ip: str = None) -> None:
        user = await self.user_repo.get_by_id(user_id)
        if user:
            await self.session_repo.revoke_all_for_user(user_id)
            await self.audit_service.log(
                tenant_id=user.tenant_id,
                user_id=user.id,
                action="USER_LOGOUT_ALL",
                resource_type="USER",
                resource_id=user.id,
                details={},
                ip=ip,
            )
            await self.session.commit()
