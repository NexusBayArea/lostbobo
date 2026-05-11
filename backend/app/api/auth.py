"""
backend/app/api/auth.py
───────────────────────
Supabase Auth with login, refresh, logout, and protected routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from backend.app.core.supabase import get_supabase_client

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

security = HTTPBearer()


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    user: dict


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> dict:
    """Verify Bearer token."""
    token = credentials.credentials
    sb = get_supabase_client()
    if not sb:
        raise HTTPException(status_code=500, detail="Auth service unavailable")

    try:
        user = sb.auth.get_user(token)
        return {
            "user_id": user.user.id,
            "email": user.user.email,
            "role": getattr(user.user, "role", None),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


@router.post("/login")
async def login(request: LoginRequest):
    sb = get_supabase_client()
    if not sb:
        raise HTTPException(status_code=500, detail="Auth service unavailable")

    try:
        response = sb.auth.sign_in_with_password({"email": request.email, "password": request.password})
        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            expires_in=response.session.expires_in,
            user={"id": response.user.id, "email": response.user.email},
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials") from e


@router.post("/refresh")
async def refresh_token(request: RefreshRequest):
    """Refresh access token."""
    sb = get_supabase_client()
    if not sb:
        raise HTTPException(status_code=500, detail="Auth service unavailable")

    try:
        response = sb.auth.refresh_session(request.refresh_token)
        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            expires_in=response.session.expires_in,
            user={"id": response.user.id, "email": response.user.email},
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from e


@router.post("/logout")
async def logout(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
):
    """Logout - revoke current session."""
    token = credentials.credentials
    sb = get_supabase_client()
    if not sb:
        raise HTTPException(status_code=500, detail="Auth service unavailable")

    try:
        sb.auth.sign_out(token)
        return {"status": "success", "message": "Logged out successfully"}
    except Exception:
        # Still return success to avoid leaking info
        return {"status": "success", "message": "Logged out"}


# Protected route example
@router.get("/me")
async def get_current_user_info(
    user: Annotated[dict, Depends(get_current_user)],
):
    return {"user": user}
