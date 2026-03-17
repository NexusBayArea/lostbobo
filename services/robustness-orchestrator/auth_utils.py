from fastapi import Header, HTTPException
from jose import jwt, JWTError
import os
import logging

logger = logging.getLogger(__name__)

# Supabase JWT Secret must be configured - raise error if missing
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
if not SUPABASE_JWT_SECRET:
    raise RuntimeError(
        "CRITICAL SECURITY: SUPABASE_JWT_SECRET environment variable is missing. "
        "The system cannot verify JWT tokens without this secret."
    )

# Supabase JWT Audience - configurable via env var, defaults to 'authenticated' for dev
SUPABASE_AUDIENCE = os.getenv("SUPABASE_AUDIENCE", "authenticated")

# Token revocation denylist (Redis-backed)
TOKEN_DENYLIST_KEY = "token_denylist"


def verify_user(authorization: str = Header(None)):
    """
    Verify Supabase JWT from Authorization header.
    Expects format: Bearer <token>

    Security Features:
    - Clock skew tolerance (30 seconds) for server time differences
    - Expiration verification enabled
    - Configurable audience validation
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Invalid Authorization Header format"
        )

    token = authorization.replace("Bearer ", "")

    # Check token against denylist (for immediate revocation)
    # Note: This requires Redis client access - implemented in api.py wrapper

    try:
        # Supabase tokens are standard JWTs
        # Options: verify_exp=True, leeway=30s for clock skew
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience=SUPABASE_AUDIENCE,
            options={
                "verify_exp": True,
                "verify_nbf": True,
                "verify_iat": True,
                "verify_aud": True,
                "verify_iss": False,  # Supabase doesn't always include issuer
                "require_exp": True,
                "require_iat": True,
            },
            leeway=30,  # 30-second clock skew tolerance
        )
        return payload  # This contains user_id as 'sub'
    except JWTError as e:
        logger.warning(f"JWT verification failed: {str(e)}")
        raise HTTPException(
            status_code=401, detail=f"Invalid or expired token: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Authentication unexpected error: {str(e)}")
        raise HTTPException(status_code=401, detail="Authentication failed")
