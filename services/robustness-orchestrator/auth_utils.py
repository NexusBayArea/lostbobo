from fastapi import Header, HTTPException
from jose import jwt, JWTError
import os

# Supabase JWT Secret should be in environment variables
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "your-supabase-jwt-secret-placeholder")

def verify_user(authorization: str = Header(None)):
    """
    Verify Supabase JWT from Authorization header.
    Expects format: Bearer <token>
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization Header format")
    
    token = authorization.replace("Bearer ", "")
    try:
        # Supabase tokens are standard JWTs
        # Audience is typically 'authenticated' for Supabase
        payload = jwt.decode(
            token, 
            SUPABASE_JWT_SECRET, 
            algorithms=["HS256"], 
            audience="authenticated"
        )
        return payload  # This contains user_id as 'sub'
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Authentication failed")
