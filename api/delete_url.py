# app/routes/url_routes.py

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.db import get_session
from utils.delete_url_and_clicks import delete_url_and_clicks
from models.models import URL
from utils.redis_client import redis_client

router = APIRouter()


@router.delete("/delete-url/{url_id}")
async def delete_url(
    url_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """
    Delete a URL and its associated clicks, and remove from Redis cache.
    """
    try:
        # Step 1: Get short_code from DB
        stmt = select(URL).where(URL.id == url_id)
        result = await session.execute(stmt)
        url = result.scalars().first()

        if not url:
            raise HTTPException(status_code=404, detail="URL not found.")

        short_code = url.short_code  # Needed to form Redis key

        # Step 2: Delete from DB and clicks
        await delete_url_and_clicks(session, url_id)

        # Step 3: Delete from Redis cache
        await redis_client.delete(f"url:{short_code}")

        return {"message": "URL and associated clicks deleted successfully"}

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error deleting URL: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete URL")
