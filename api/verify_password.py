from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import bcrypt
from datetime import datetime, timezone
from uuid import uuid4

from models.models import URL, Click
from database.db import get_session, async_session_maker
from schemas.dashboard import VerifyPasswordRequest
from utils.geoip import get_country_and_flag
from utils.delete_url_and_clicks import delete_url_and_clicks

router = APIRouter()

@router.post("/verify-password")
async def verify_password(
    payload: VerifyPasswordRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    stmt = select(URL).where(URL.short_code == payload.short_code)
    result = await session.execute(stmt)
    url = result.scalars().first()

    if not url:
        raise HTTPException(status_code=404, detail="Short URL not found.")

    if not url.is_protected or not url.password_hash:
        raise HTTPException(
            status_code=400, detail="URL is not protected or has no password."
        )

    if not bcrypt.checkpw(
        payload.password.encode("utf-8"), url.password_hash.encode("utf-8")
    ):
        raise HTTPException(status_code=401, detail="Incorrect password.")

    # Check expiry
    if url.expires_at and url.expires_at.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc):
        background_tasks.add_task(delete_url_and_clicks, None, str(url.id))
        raise HTTPException(status_code=410, detail="URL expired.")

    # Check click limit
    if url.click_limit == 0:
        background_tasks.add_task(delete_url_and_clicks, None, str(url.id))
        raise HTTPException(status_code=404, detail="Click limit reached.")

    # Record click
    background_tasks.add_task(record_click, url.id, request)

    # Deduct click limit
    if url.click_limit is not None:
        background_tasks.add_task(deduct_click_limit, url.id)

    return {"destination": url.destination}


# Utility (same as in redirect handler)
async def record_click(url_id: str, request: Request):
    async with async_session_maker() as session:
        country, flag = await get_country_and_flag(request)
        click = Click(
            id=uuid4(),
            url_id=url_id,
            country=country,
            flag=flag,
            timestamp=datetime.now(timezone.utc),
        )
        session.add(click)
        await session.commit()

async def deduct_click_limit(url_id: str):
    async with async_session_maker() as session:
        stmt = select(URL).where(URL.id == url_id)
        result = await session.execute(stmt)
        url = result.scalars().first()

        if not url or url.click_limit is None:
            return

        url.click_limit -= 1

        if url.click_limit <= 0:
            await delete_url_and_clicks(session, url_id)
        else:
            await session.commit()
