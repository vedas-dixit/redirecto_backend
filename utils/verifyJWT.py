from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import APIRouter, HTTPException, Depends
import os
import jwt
from jwt import PyJWTError
from typing import Optional

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
security = HTTPBearer()


async def verify_supabase_token(
    credentials: HTTPAuthorizationCredentials,
) -> Optional[dict]:
    """
    Verify Supabase JWT token and return user info.
    Returns None if token is invalid, raises HTTPException for other errors.
    """
    if not credentials or not credentials.credentials:
        return None

    token = credentials.credentials

    if not SUPABASE_JWT_SECRET:
        print("SUPABASE_JWT_SECRET not configured")
        raise HTTPException(status_code=500, detail="JWT verification not configured")

    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )

        # Additional validation
        if not payload.get("sub"):
            print("JWT missing required 'sub' claim")
            return None

        print(f"JWT verified for user: {payload.get('email', 'Unknown')}")
        return payload

    except jwt.ExpiredSignatureError:
        print("JWT token has expired")
        return None
    except jwt.InvalidAudienceError:
        print("JWT invalid audience")
        return None
    except jwt.InvalidSignatureError:
        print("JWT invalid signature")
        return None
    except PyJWTError as e:
        print(f"JWT verification failed: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error during JWT verification: {str(e)}")
        raise HTTPException(status_code=500, detail="Authentication service error")
