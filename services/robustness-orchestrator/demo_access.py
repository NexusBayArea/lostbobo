"""
SimHPC Magic Link Demo Access System

Supabase-backed magic link demo access with usage limits.
Provides secure, single-use demo tokens with configurable run limits
and expiration dates for alpha pilot onboarding.

Endpoints:
  POST /api/v1/demo/magic-link   - Validate a magic link token
  GET  /api/v1/demo/usage        - Check remaining demo runs
  POST /api/v1/demo/use-run      - Decrement usage count
  POST /api/v1/demo/create       - Admin: Generate new demo link
"""

import os
import hashlib
import secrets
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# --- Supabase Client ---
try:
    from supabase import create_client, Client
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    supabase_client: Optional[Client] = None
    if SUPABASE_URL and SUPABASE_SERVICE_KEY:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        logger.info("Supabase client initialized for demo access")
    else:
        logger.warning("Supabase credentials not configured — demo_access table unavailable")
except ImportError:
    supabase_client = None
    logger.warning("supabase-py not installed — demo system uses Redis fallback")

# --- Redis Fallback ---
import redis
import json

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r_client = redis.from_url(REDIS_URL, decode_responses=True)

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
        result = supabase_client.table("demo_access") \
            .select("*") \
            .eq("token_hash", token_hash) \
            .single() \
            .execute()
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
        supabase_client.table("demo_access") \
            .update({"usage_count": new_count}) \
            .eq("id", row_id) \
            .execute()
    except Exception as e:
        logger.error(f"Supabase demo update error: {e}")


def _update_demo_usage_redis(token_hash: str, demo_data: dict):
    """Update demo data in Redis."""
    r_client.setex(
        f"demo:{token_hash}",
        DEMO_EXPIRY_DAYS * 86400,
        json.dumps(demo_data)
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


# --- Router ---

router = APIRouter(prefix="/api/v1/demo", tags=["Demo Access"])


@router.post("/magic-link", response_model=MagicLinkResponse)
async def validate_magic_link(request: MagicLinkRequest, req: Request):
    """
    Validate a magic demo link token.
    Called when user clicks the demo link (GET /demo/{token} on frontend).
    """
    token = request.token.strip()
    if not token or len(token) < 16:
        return MagicLinkResponse(valid=False, reason="invalid", message="Invalid token format")
    
    # Log access attempt
    client_ip = req.client.host if req.client else "unknown"
    logger.info(f"Demo magic link validation from IP {client_ip}")
    
    data = get_demo_data(token)
    if not data:
        return MagicLinkResponse(valid=False, reason="invalid", message="Token not recognized")
    
    is_valid, reason = validate_demo(data)
    
    if not is_valid:
        return MagicLinkResponse(
            valid=False, 
            reason=reason,
            message={
                "limit_reached": "All demo simulations have been used.",
                "expired": "This demo link has expired.",
            }.get(reason, "Invalid token")
        )
    
    remaining = data.get("usage_limit", DEMO_DEFAULT_LIMIT) - data.get("usage_count", 0)
    
    return MagicLinkResponse(
        valid=True,
        remaining=remaining,
        usage_limit=data.get("usage_limit", DEMO_DEFAULT_LIMIT),
        email=data.get("email"),
    )


@router.get("/usage", response_model=DemoUsageResponse)
async def get_demo_usage(x_demo_token: str = Header(None)):
    """Get remaining demo runs for the given token."""
    if not x_demo_token:
        raise HTTPException(status_code=400, detail="Missing X-Demo-Token header")
    
    data = get_demo_data(x_demo_token)
    if not data:
        return DemoUsageResponse(remaining=0, limit=0, used=0, expired=True)
    
    is_valid, reason = validate_demo(data)
    usage_count = data.get("usage_count", 0)
    usage_limit = data.get("usage_limit", DEMO_DEFAULT_LIMIT)
    remaining = max(0, usage_limit - usage_count)
    
    return DemoUsageResponse(
        remaining=remaining,
        limit=usage_limit,
        used=usage_count,
        expired=(reason == "expired") if not is_valid else False
    )


@router.post("/use-run", response_model=UseRunResponse)
async def use_demo_run(x_demo_token: str = Header(None)):
    """
    Decrement a demo run. Called before each simulation.
    Returns success=False if limit is reached.
    """
    if not x_demo_token:
        raise HTTPException(status_code=400, detail="Missing X-Demo-Token header")
    
    data = get_demo_data(x_demo_token)
    if not data:
        return UseRunResponse(success=False, remaining=0)
    
    is_valid, reason = validate_demo(data)
    if not is_valid:
        return UseRunResponse(success=False, remaining=0)
    
    # Increment usage
    new_count = data.get("usage_count", 0) + 1
    usage_limit = data.get("usage_limit", DEMO_DEFAULT_LIMIT)
    remaining = max(0, usage_limit - new_count)
    
    token_hash = hash_token(x_demo_token)
    
    # Update in Supabase
    row_id = data.get("id")
    if row_id and supabase_client:
        _update_demo_usage_supabase(row_id, new_count)
    
    # Always update Redis (for fast reads)
    data["usage_count"] = new_count
    _update_demo_usage_redis(token_hash, data)
    
    logger.info(f"Demo run used: {new_count}/{usage_limit} for {data.get('email', 'unknown')}")
    
    return UseRunResponse(success=True, remaining=remaining)


@router.post("/create", response_model=CreateDemoResponse)
async def create_demo_link(
    request: CreateDemoRequest,
    x_api_key: str = Header(None),
    req: Request = None
):
    """
    Admin endpoint: Generate a new magic demo link.
    Requires SIMHPC_API_KEY or SIMHPC_ADMIN_SECRET.
    """
    # Verify admin access
    if not ADMIN_SECRET or x_api_key != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Generate secure token
    token = secrets.token_hex(32)
    token_hash = hash_token(token)
    
    expires_at = datetime.now(timezone.utc) + timedelta(days=request.expiry_days)
    
    demo_data = {
        "email": request.email,
        "token_hash": token_hash,
        "usage_limit": request.usage_limit,
        "usage_count": 0,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    # Store in Supabase
    if supabase_client:
        try:
            supabase_client.table("demo_access").insert(demo_data).execute()
            logger.info(f"Demo link created in Supabase for {request.email}")
        except Exception as e:
            logger.error(f"Supabase insert error: {e}")
            # Fall through to Redis
    
    # Also store in Redis for fast access
    _update_demo_usage_redis(token_hash, demo_data)
    
    link = f"https://simhpc.com/demo/{token}"
    
    logger.info(f"Magic demo link generated for {request.email}: {link}")
    
    return CreateDemoResponse(
        link=link,
        token=token,
        email=request.email,
        usage_limit=request.usage_limit,
        expires_at=expires_at.isoformat(),
    )
