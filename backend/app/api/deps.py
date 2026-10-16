from __future__ import annotations

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_settings
from app.core.errors import AuthenticationError
from app.core.security import decode_access_token
from app.repositories import users

_bearer = HTTPBearer(auto_error=False)


async def current_user(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    settings: Settings = Depends(get_settings),
) -> dict:
    if creds is None or creds.scheme.lower() != "bearer":
        raise AuthenticationError("Authentication required.", headers={"WWW-Authenticate": "Bearer"})
    claims = decode_access_token(settings, creds.credentials)
    user = await users.get_by_id(claims.sub)
    if not user or not user["is_active"]:
        raise AuthenticationError("Account not found or disabled.")
    request.state.user_id = user["id"]
    return user
