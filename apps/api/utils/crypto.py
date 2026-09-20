import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt, JWTError

from apps.api.config import settings

# Configure bcrypt with cost factor 12
pwd_context = CryptContext(
    schemes=["bcrypt", "argon2", "md5", "sha1", "plaintext"],
    deprecated=["argon2", "md5", "sha1", "plaintext"],
    bcrypt__rounds=12,
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hash: str) -> bool:
    # Use constant time comparison inside passlib.verify
    return pwd_context.verify(password, hash)


def check_needs_rehash(hash: str) -> bool:
    return pwd_context.needs_update(hash)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def create_refresh_token() -> tuple[str, str]:
    raw_token = secrets.token_urlsafe(32)
    hashed_token = hash_token(raw_token)
    return raw_token, hashed_token


def verify_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError as err:
        raise ValueError("Invalid token") from err


def generate_secure_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
