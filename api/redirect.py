from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import uuid4
from datetime import datetime, timezone
from utils.geoip import get_country_and_flag
from utils.delete_url_and_clicks import delete_url_and_clicks
from models.models import URL, Click
from database.db import async_session_maker, get_session

router = APIRouter()


@router.get("/{short_code}")
async def handle_redirect(
    short_code: str,
    request: Request,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    # Find URL
    stmt = select(URL).where(URL.short_code == short_code)
    result = await session.execute(stmt)
    url = result.scalars().first()

    if not url:
        raise HTTPException(status_code=404, detail="Short URL not found.")

    # Check for expiry
    if url.expires_at and url.expires_at.replace(tzinfo=timezone.utc) <= datetime.now(
        timezone.utc
    ):
        background_tasks.add_task(delete_url_and_clicks, None, str(url.id))
        raise HTTPException(status_code=410, detail="URL expired.")

    # Check for click limit
    if url.click_limit == 0:
        background_tasks.add_task(delete_url_and_clicks, None, str(url.id))
        raise HTTPException(status_code=404, detail="Click limit reached.")

    frontend_base_url = "http://localhost:3000"

    if url.is_protected:
        return RedirectResponse(
            url=f"{frontend_base_url}/secure/{short_code}", status_code=307
        )

    # Allow redirect → record click & deduct click count in background
    background_tasks.add_task(record_click, url.id, request)

    if url.click_limit is not None:
        background_tasks.add_task(deduct_click_limit, url.id)

    # Redirect
    return RedirectResponse(url=url.destination, status_code=307)


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
