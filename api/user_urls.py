from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from utils.verifyJWT import verify_supabase_token
from api.users import create_user_if_not_exists
from database.db import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from utils.addUrl import add_url_for_user
from schemas.dashboard import CreateUrlResponse, CreateUrlRequest
import uuid

router = APIRouter()
security = HTTPBearer(auto_error=False)  # Don't auto-error, we'll handle manually
load_dotenv()


@router.post("/create-url", response_model=CreateUrlResponse)
async def create_url(
    request: CreateUrlRequest,
    session: AsyncSession = Depends(get_session),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_guest_uuid: Optional[str] = Header(None, alias="X-Guest-UUID"),
):
    """
    Create a shortened URL — supports guests and authenticated users.
    FAANG-level security: JWT verification determines user type, not frontend flags.
    """

    user_data = None
    is_authenticated = False

    # Step 1: Try to authenticate if token is provided
    if credentials and credentials.credentials:
        try:
            user_data = await verify_supabase_token(credentials)
            if user_data:
                is_authenticated = True
        except HTTPException:
            # Token is invalid, treat as guest
            print("Invalid token provided, falling back to guest")
            pass

    # Step 2: Handle guest flow
    if not is_authenticated:
        # Validate guest UUID
        if not x_guest_uuid:
            raise HTTPException(
                status_code=400, detail="Guest requests require X-Guest-UUID header"
            )

        try:
            # Validate UUID format
            uuid.UUID(x_guest_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid X-Guest-UUID format")

        print(f"Guest request with UUID: {x_guest_uuid}")

    # Step 3: Prepare user payload based on authentication status
    if is_authenticated:
        # Authenticated user - extract from JWT
        user_payload = {
            "id": user_data.get("sub"),  # Supabase uses 'sub' for user ID
            "is_guest": False,  # JWT verified = not guest
            "email": user_data.get("email"),
            "name": user_data.get("user_metadata", {}).get("name"),
            "avatar_url": user_data.get("user_metadata", {}).get("avatar_url"),
            "provider": user_data.get("app_metadata", {}).get("provider"),
            "provider_id": user_data.get("sub"),
        }
    else:
        # Guest user - create guest payload
        user_payload = {
            "id": x_guest_uuid,  # Use guest UUID as ID
            "is_guest": True,
            "email": None,
            "name": f"Guest-{x_guest_uuid[:8]}",  # Friendly guest name
            "avatar_url": None,
            "provider": "guest",
            "provider_id": x_guest_uuid,
        }

    try:
        # Step 4: Ensure user exists in DB
        db_user = await create_user_if_not_exists(user_payload, session)

        # Step 5: Create the shortened URL
        new_url = await add_url_for_user(
            session=session,
            user_id=db_user.id,
            long_url=request.long_url,
            expires_at=request.expires_at,
            click_limit=request.click_limit,
            password=request.password,
            is_guest=user_payload["is_guest"],  # Server-determined, not client
            is_protected=request.is_protected,
        )

        return CreateUrlResponse(
            short_url=new_url.short_code,
            long_url=new_url.destination,
            user_id=str(db_user.id),
        )
    except HTTPException:
        # Let HTTPExceptions bubble up with their original status codes
        raise
    except Exception as e:
        print(f"Error creating URL: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create URL")
