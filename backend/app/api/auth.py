"""Full Supabase Auth Integration."""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from backend.app.core.supabase import get_supabase_client

log = logging.getLogger(__name__)

_JWT_SECRET = os.environ.get("JWT_SECRET", "")
_JWT_EXPIRY_HOURS = int(os.environ.get("JWT_EXPIRY_HOURS", "8"))
_ENV = os.environ.get("SIMHPC_ENV", "production").lower()

if _ENV != "test" and not _JWT_SECRET:
    raise OSError(
        "JWT_SECRET environment variable is not set. "
        'Generate one with: python -c "import secrets; print(secrets.token_hex(32))"'
    )

router = APIRouter(prefix="/api/auth", tags=["auth"])
_bearer = HTTPBearer(auto_error=False)


class AuthUser(BaseModel):
    id: str
    email: str
    role: str = "user"
    tenant_id: str = "public"


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    token: str
    user: AuthUser


def _create_token(user: AuthUser) -> str:
    import jwt

    payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "tenant_id": user.tenant_id,
        "exp": datetime.now(UTC) + timedelta(hours=_JWT_EXPIRY_HOURS),
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, _JWT_SECRET, algorithm="HS256")


def _decode_token(token: str) -> dict:
    import jwt
    from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

    try:
        return jwt.decode(token, _JWT_SECRET, algorithms=["HS256"])
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired — please sign in again",
        )
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> AuthUser:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    claims = _decode_token(credentials.credentials)
    return AuthUser(
        id=claims["sub"],
        email=claims["email"],
        role=claims.get("role", "user"),
        tenant_id=claims.get("tenant_id", "public"),
    )


_ROLE_RANK = {"viewer": 0, "user": 1, "admin": 2}


def require_role(minimum_role: str):
    async def _check(user: AuthUser = Depends(get_current_user)) -> AuthUser:
        user_rank = _ROLE_RANK.get(user.role, 0)
        required_rank = _ROLE_RANK.get(minimum_role, 99)
        if user_rank < required_rank:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{minimum_role}' required, you have '{user.role}'",
            )
        return user

    return _check


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest) -> LoginResponse:
    user = await _verify_credentials(body.email, body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = _create_token(user)
    log.info("Login: user=%s tenant=%s role=%s", user.email, user.tenant_id, user.role)
    return LoginResponse(token=token, user=user)


@router.get("/me", response_model=AuthUser)
async def me(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(user: AuthUser = Depends(get_current_user)) -> None:
    log.info("Logout: user=%s", user.email)


async def _verify_credentials(email: str, password: str) -> AuthUser | None:
    """Real Supabase auth call."""
    sb = get_supabase_client()
    if sb is None:
        log.warning("Supabase client is None — test mode?")
        return None

    try:
        resp = sb.auth.sign_in_with_password({"email": email, "password": password})

        if resp.user is None:
            return None

        user_metadata = resp.user.user_metadata or {}

        return AuthUser(
            id=resp.user.id,
            email=resp.user.email or email,
            role=user_metadata.get("role", "user"),
            tenant_id=user_metadata.get("tenant_id", "public"),
        )
    except Exception as exc:
        log.error(f"Supabase auth failed for {email}: {exc}")
        return None
