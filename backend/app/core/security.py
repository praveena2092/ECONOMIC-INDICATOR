"""Password hashing and JWT helpers."""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass

import jwt
from passlib.context import CryptContext

from app.core.config import Settings
from app.core.errors import AuthenticationError

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Used to keep login timing similar when the e-mail is unknown.
DUMMY_HASH = _pwd.hash("not-a-real-password")


def hash_password(password: str) -> str:
    return _pwd.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _pwd.verify(password, password_hash)
    except ValueError:
        return False


@dataclass(frozen=True)
class TokenClaims:
    sub: str
    role: str
    exp: int


def create_access_token(settings: Settings, *, user_id: str, role: str) -> tuple[str, int]:
    now = int(time.time())
    ttl = settings.access_token_minutes * 60
    payload = {"sub": user_id, "role": role, "iat": now, "exp": now + ttl, "jti": uuid.uuid4().hex}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm), ttl


def decode_access_token(settings: Settings, token: str) -> TokenClaims:
    try:
        data = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub", "iat"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationError("Session expired. Please sign in again.") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError("Invalid authentication token.") from exc
    return TokenClaims(sub=str(data["sub"]), role=str(data.get("role", "viewer")), exp=int(data["exp"]))
