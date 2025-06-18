from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.models import URL
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from datetime import datetime, timedelta, timezone
from utils.generateUrl import generate_short_code
from typing import Optional
from utils.hash_password import hash_password


async def add_url_for_user(
    *,
    session: AsyncSession,
    user_id: str,
    long_url: str,
    is_guest: bool,
    expires_at: Optional[str] = None,
    click_limit: Optional[int] = None,
    password: Optional[str] = None,
    is_protected: Optional[bool] = False,
) -> URL:

    try:
        # Step 1: Check if this user has already shortened this URL
        stmt = select(URL).where(URL.user_id == user_id, URL.destination == long_url)
        result = await session.execute(stmt)
        existing_url = result.scalars().first()

        if existing_url:
            raise HTTPException(
                status_code=409, detail="URL already shortened by this user."
            )

        # Step 2: Count how many URLs this user has created
        count_stmt = select(URL).where(URL.user_id == user_id)
        result = await session.execute(count_stmt)
        user_urls = result.scalars().all()

        # Step 2.5: Enforce guest URL limit
        if is_guest and len(user_urls) >= 5:
            raise HTTPException(
                status_code=403, detail="Guest user limit exceeded (max 5 URLs)"
            )

        # Step 3: Generate unique short code based on index
        short_code = generate_short_code(user_id, len(user_urls) + 1)
        expires_at = (
            datetime.strptime(expires_at, "%Y-%m-%d")
            if isinstance(expires_at, str)
            else None
        )

        # Step 4: Create the new URL object
        password_hash = None
        if is_protected and password:
            password_hash = hash_password(password)

        # Step 4: Create the new URL object
        now_utc = datetime.now(timezone.utc)
        new_url = URL(
            user_id=user_id,
            short_code=short_code,
            destination=long_url,
            is_protected=is_protected,
            password_hash=password_hash,
            expires_at=expires_at,
            click_limit=click_limit,
            created_at=now_utc,
        )

        session.add(new_url)
        await session.commit()
        await session.refresh(new_url)

        return new_url

    except HTTPException:
        # Re-raise HTTPExceptions so they bubble up with proper status codes
        await session.rollback()
        raise

    except SQLAlchemyError as e:
        await session.rollback()
        print(f"Database error in add_url_for_user: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")

    except Exception as e:
        await session.rollback()
        print(f"Unexpected error in add_url_for_user: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
