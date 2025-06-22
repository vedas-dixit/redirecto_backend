from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import uuid4
from datetime import datetime, timezone
from utils.geoip import get_country_and_flag
from utils.delete_url_and_clicks import delete_url_and_clicks
from models.models import URL, Click
from utils.redis_client import redis_client
from database.db import async_session_maker, get_session
from dotenv import load_dotenv
import os

router = APIRouter()
load_dotenv()
WEB_BASE_URL = os.getenv("WEB_BASE_URL")


@router.get("/{short_code}")
async def handle_redirect(
    short_code: str,
    request: Request,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    redis_key = f"url:{short_code}"
    url_data = await redis_client.hgetall(redis_key)

    if not url_data:
        # Not in Redis, fetch from DB
        stmt = select(URL).where(URL.short_code == short_code)
        result = await session.execute(stmt)
        url = result.scalars().first()

        if not url:
            raise HTTPException(status_code=404, detail="Short URL not found")

        # Store in Redis (cache)
        await redis_client.hset(
            redis_key,
            mapping={
                "id": str(url.id),
                "destination": url.destination,
                "expires_at": str(url.expires_at) if url.expires_at else "",
                "click_limit": url.click_limit if url.click_limit is not None else "",
                "is_protected": str(url.is_protected),
            },
        )
        if url.expires_at:
            ttl = int((url.expires_at - datetime.now(timezone.utc)).total_seconds())
            await redis_client.expire(redis_key, ttl)
    else:
        url = type("URLObj", (), {})()
        url.id = url_data["id"]
        url.destination = url_data["destination"]
        url.expires_at = (
            datetime.fromisoformat(url_data["expires_at"])
            if url_data.get("expires_at")
            else None
        )
        url.click_limit = (
            int(url_data["click_limit"])
            if url_data.get("click_limit") not in ("", None)
            else None
        )
        url.is_protected = url_data["is_protected"] == "True"

    # Expiry
    if url.expires_at and url.expires_at <= datetime.now(timezone.utc):
        background_tasks.add_task(delete_url_and_clicks, None, str(url.id))
        await redis_client.delete(redis_key)
        raise HTTPException(status_code=410, detail="URL expired.")

    # Click limit
    if url.click_limit == 0:
        background_tasks.add_task(delete_url_and_clicks, None, str(url.id))
        await redis_client.delete(redis_key)
        raise HTTPException(status_code=404, detail="Click limit reached.")

    # Protected
    if url.is_protected:
        return RedirectResponse(url=f"{WEB_BASE_URL}/{short_code}", status_code=307)

    background_tasks.add_task(record_click, url.id, request)

    if url.click_limit is not None:
        background_tasks.add_task(
            deduct_click_limit_and_update_cache, url.id, short_code
        )

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


async def deduct_click_limit_and_update_cache(url_id: str, short_code: str):
    async with async_session_maker() as session:
        stmt = select(URL).where(URL.id == url_id)
        result = await session.execute(stmt)
        url = result.scalars().first()

        if not url or url.click_limit is None:
            return

        url.click_limit -= 1

        if url.click_limit <= 0:
            await delete_url_and_clicks(session, url_id)
            await redis_client.delete(f"url:{short_code}")
        else:
            await session.commit()
            # Update Redis cache
            await redis_client.hset(
                f"url:{short_code}", mapping={"click_limit": url.click_limit}
            )
