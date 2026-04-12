"""
SimHPC Magic Link Demo Access System

Supabase-backed magic link demo access with usage limits.
Provides secure, single-use demo tokens with configurable run limits
and expiration dates for alpha pilot onboarding.
"""

import hashlib
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from pydantic import BaseModel, Field

from app.core.config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)

# --- Supabase Client ---
try:
    from supabase import Client, create_client

    supabase_client: Optional[Client] = None
    if settings.APP_URL and settings.API_TOKEN:
        supabase_client = create_client(settings.APP_URL, settings.API_TOKEN)
        logger.info("Supabase client initialized for demo access")
    else:
        logger.warning(
            "Infrastructure secrets (SB_*) not correctly normalized — demo_access table unavailable"
        )
except ImportError:
    supabase_client = None
    logger.warning("supabase-py not installed — demo system uses Redis fallback")

# --- Redis Fallback ---
import json  # noqa: E402
import redis  # noqa: E402

r_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

# --- Config ---
DEMO_DEFAULT_LIMIT = int(os.getenv("DEMO_USAGE_LIMIT", "5"))
DEMO_EXPIRY_DAYS = int(os.getenv("DEMO_EXPIRY_DAYS", "7"))
ADMIN_SECRET = os.getenv("SIMHPC_ADMIN_SECRET", os.getenv("SIMHPC_API_KEY", ""))

# --- Models ---


class MagicLinkRequest(BaseModel):
    token: str = Field(..., description="Magic link demo token")


class MagicLinkResponse(BaseModel):
    valid: bool
    remaining: Optional[int] = None
    usage_limit: Optional[int] = None
    email: Optional[str] = None
    reason: Optional[str] = None
    message: Optional[str] = None


class DemoUsageResponse(BaseModel):
    remaining: int
    limit: int
    used: int
    expired: bool


class UseRunResponse(BaseModel):
    success: bool
    remaining: int


class CreateDemoRequest(BaseModel):
    email: str = Field(..., description="Pilot email address")
    usage_limit: int = Field(default=5, ge=1, le=100)
    expiry_days: int = Field(default=7, ge=1, le=90)


class CreateDemoResponse(BaseModel):
    link: str
    token: str
    email: str
    usage_limit: int
    expires_at: str


# --- Helpers ---


def hash_token(token: str) -> str:
    """SHA-256 hash for secure storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def _get_demo_via_supabase(token_hash: str) -> Optional[dict]:
    """Look up demo_access row by hashed token."""
    if not supabase_client:
        return None
    try:
        result = (
            supabase_client.table("demo_access")
            .select("*")
            .eq("token_hash", token_hash)
            .single()
            .execute()
        )
        return result.data
    except Exception as e:
        logger.error(f"Supabase demo lookup error: {e}")
        return None


def _get_demo_via_redis(token_hash: str) -> Optional[dict]:
    """Fallback: look up demo in Redis."""
    data = r_client.get(f"demo:{token_hash}")
    if data:
        return json.loads(data)
    return None


def _update_demo_usage_supabase(row_id: str, new_count: int):
    """Increment usage_count in Supabase."""
    if not supabase_client:
        return
    try:
        supabase_client.table("demo_access").update({"usage_count": new_count}).eq(
            "id", row_id
        ).execute()
    except Exception as e:
        logger.error(f"Supabase demo update error: {e}")


def _update_demo_usage_redis(token_hash: str, demo_data: dict):
    """Update demo data in Redis."""
    r_client.setex(
        f"demo:{token_hash}", DEMO_EXPIRY_DAYS * 86400, json.dumps(demo_data)
    )


def get_demo_data(token: str) -> Optional[dict]:
    """Get demo data from Supabase or Redis fallback."""
    token_hash = hash_token(token)

    # Try Supabase first
    data = _get_demo_via_supabase(token_hash)
    if data:
        return data

    # Redis fallback
    return _get_demo_via_redis(token_hash)


def validate_demo(data: dict) -> tuple[bool, Optional[str]]:
    """Validate demo entry. Returns (is_valid, reason_if_invalid)."""
    if not data:
        return False, "invalid"

    # Check usage limit
    usage_count = data.get("usage_count", 0)
    usage_limit = data.get("usage_limit", DEMO_DEFAULT_LIMIT)
    if usage_count >= usage_limit:
        return False, "limit_reached"

    # Check expiration
    expires_at = data.get("expires_at")
    if expires_at:
        if isinstance(expires_at, str):
            try:
                exp = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            except ValueError:
                exp = datetime.now(timezone.utc) + timedelta(days=1)
        else:
            exp = expires_at

        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)

        if datetime.now(timezone.utc) > exp:
            return False, "expired"

    return True, None
