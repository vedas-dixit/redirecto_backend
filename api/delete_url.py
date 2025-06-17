# app/routes/url_routes.py

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import get_session
from utils.delete_url_and_clicks import delete_url_and_clicks

router = APIRouter()


@router.delete("/delete-url/{url_id}")
async def delete_url(
    url_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """
    Delete a URL and its associated clicks.
    """
    try:
        await delete_url_and_clicks(session, url_id)
        return {"message": "URL and associated clicks deleted successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error deleting URL: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete URL")
