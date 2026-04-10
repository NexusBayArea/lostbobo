from fastapi import Header, HTTPException
from jose import jwt, JWTError
import os
import logging

logger = logging.getLogger(__name__)

# Mandatory Secret - The system will fail fast if not configured
SB_JWT_SECRET = os.getenv("SB_JWT_SECRET")
if not SB_JWT_SECRET:
    raise RuntimeError(
        "CRITICAL SECURITY: SB_JWT_SECRET is missing. "
        "JWT verification is disabled until this secret is set."
    )

SB_AUDIENCE = os.getenv("SB_AUDIENCE", "authenticated")


def verify_user(authorization: str = Header(None)):
    """
    Verifies Supabase JWT with 30s leeway and audience validation.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")

    token = authorization.replace("Bearer ", "")

    try:
        payload = jwt.decode(
            token,
            SB_JWT_SECRET,
            algorithms=["HS256"],
            audience=SB_AUDIENCE,
            options={
                "verify_exp": True,
                "verify_aud": True,
                "require_exp": True,
            },
            leeway=30,  # Handles server clock drift
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT Verification Failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Session expired or invalid") from e
