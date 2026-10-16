from fastapi import APIRouter, Depends, Request

from app.api.deps import current_user
from app.api.rate_limit import login_limiter
from app.core.config import Settings, get_settings
from app.core.errors import AuthenticationError
from app.core.security import DUMMY_HASH, create_access_token, verify_password
from app.repositories import users
from app.schemas.auth import LoginRequest, TokenResponse, UserOut
from app.schemas.dashboard import ErrorResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse, summary="Sign in and get a JWT",
             responses={401: {"model": ErrorResponse, "description": "Incorrect e-mail or password"},
                        429: {"model": ErrorResponse, "description": "Too many attempts (5 per minute)"}})
async def login(body: LoginRequest, request: Request, settings: Settings = Depends(get_settings)):
    email = body.email.strip().lower()
    key = f"{request.client.host if request.client else 'unknown'}:{email}"
    login_limiter.check(key)

    user = await users.get_by_email(email)
    # Always run a hash verification so response time doesn't reveal whether the e-mail exists.
    ok = verify_password(body.password, user["password_hash"] if user else DUMMY_HASH)
    if not (user and ok and user["is_active"]):
        raise AuthenticationError("Incorrect e-mail or password.")

    login_limiter.reset(key)
    await users.touch_login(user["id"])
    token, ttl = create_access_token(settings, user_id=user["id"], role=user["role"])
    return TokenResponse(access_token=token, expires_in=ttl)


@router.get("/me", response_model=UserOut, summary="Current user",
            responses={401: {"model": ErrorResponse, "description": "Missing, invalid or expired token"}})
async def me(user: dict = Depends(current_user)):
    return UserOut(id=user["id"], email=user["email"], role=user["role"])