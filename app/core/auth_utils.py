import logging

from fastapi import Header, HTTPException
from jose import JWTError, jwt
from app.core.config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)


def verify_user(authorization: str = Header(None)):
    """
    Verifies Supabase JWT with 30s leeway and audience validation.
    Uses normalized application settings.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")

    token = authorization.replace("Bearer ", "")

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=["HS256"],
            audience=settings.JWT_AUDIENCE,
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
