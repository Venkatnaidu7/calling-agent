from typing import Callable, Sequence
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.database import get_db
from apps.api.utils.crypto import verify_access_token
from apps.api.models import User, Tenant
from apps.api.repositories.user_repo import UserRepository
from apps.api.repositories.tenant_repo import TenantRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

ROLE_PERMISSIONS = {
    "PLATFORM_ADMIN": ["*"],
    "TENANT_OWNER": ["manage_tenant", "manage_users", "manage_billing", "view_all", "edit_all"],
    "TENANT_ADMIN": ["manage_users", "view_all", "edit_all"],
    "SUPERVISOR": ["view_all", "manage_agents"],
    "AGENT_MANAGER": ["manage_agents", "view_calls"],
    "CAMPAIGN_MANAGER": ["view_all", "manage_campaigns"],
    "COMPLIANCE_MANAGER": ["view_all", "manage_compliance"],
    "CONTACT_MANAGER": ["view_all", "manage_contacts"],
    "ANALYST": ["view_analytics", "view_calls"],
    "READ_ONLY": ["view_all"]
}

async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = verify_access_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
        
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
        
    tenant_repo = TenantRepository(session)
    tenant = await tenant_repo.get_by_id(user.tenant_id)
    if tenant is None or tenant.status != "active":
        raise HTTPException(status_code=403, detail="Tenant is inactive")
        
    return user

def require_roles(*allowed_roles: str | list[str]) -> Callable:
    # Flatten if a single list was passed: require_roles(["A", "B"]) → ("A", "B")
    if len(allowed_roles) == 1 and isinstance(allowed_roles[0], (list, tuple)):
        allowed_roles = tuple(allowed_roles[0])

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles and current_user.role != "PLATFORM_ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted"
            )
        return current_user
    return role_checker

def require_permissions(*permissions: str) -> Callable:
    async def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        user_perms = ROLE_PERMISSIONS.get(current_user.role, [])
        if "*" in user_perms:
            return current_user
            
        for perm in permissions:
            if perm not in user_perms:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permission: {perm}"
                )
        return current_user
    return permission_checker
