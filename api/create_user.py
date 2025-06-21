from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from utils.verifyJWT import verify_supabase_token
from api.users import create_user_if_not_exists
from database.db import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from utils.funny_names import FUNNY_NAMES  # Import your funny names dict
import uuid
import random

router = APIRouter()
security = HTTPBearer(auto_error=False)  # Don't auto-error, we'll handle manually
load_dotenv()


class CreateUserResponse(BaseModel):
    user_id: str
    is_guest: bool
    email: Optional[str]
    name: Optional[str]
    avatar_url: Optional[str]
    provider: str
    message: str


@router.post("/create-user", response_model=CreateUserResponse)
async def create_user(
    session: AsyncSession = Depends(get_session),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_guest_uuid: Optional[str] = Header(None, alias="X-Guest-UUID"),
):
    """
    Create or retrieve a user — supports guests and authenticated users.
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
        # Guest user - create guest payload with funny random name
        funny_name = random.choice(list(FUNNY_NAMES.values()))  # Pick random funny name
        user_payload = {
            "id": x_guest_uuid,  # Use guest UUID as ID
            "is_guest": True,
            "email": None,
            "name": funny_name,  # Random funny name instead of boring Guest-12345
            "avatar_url": None,
            "provider": "guest",
            "provider_id": x_guest_uuid,
        }

    try:
        # Step 4: Create or retrieve user from DB
        db_user = await create_user_if_not_exists(user_payload, session)

        # Step 5: Return user information
        return CreateUserResponse(
            user_id=str(db_user.id),
            is_guest=db_user.is_guest,
            email=db_user.email,
            name=db_user.name,
            avatar_url=db_user.avatar_url,
            provider=db_user.provider,
            message=(
                "User created successfully"
                if not hasattr(db_user, "_was_existing")
                else "User already exists"
            ),
        )

    except HTTPException:
        # Let HTTPExceptions bubble up with their original status codes
        raise
    except Exception as e:
        print(f"Error creating/retrieving user: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create or retrieve user")
