from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from models.models import Click, URL
from fastapi import HTTPException


async def delete_url_and_clicks(session: AsyncSession | None, url_id: str) -> None:
    """
    Deletes all Clicks and the URL record for a given URL ID.
    If no session is passed (None), it creates its own session.
    """

    async def _delete_within_session(sess: AsyncSession):
        await sess.execute(delete(Click).where(Click.url_id == url_id))
        result = await sess.execute(delete(URL).where(URL.id == url_id))

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="URL not found")

        await sess.commit()

    if session:
        await _delete_within_session(session)
    else:
        from database.db import async_session_maker
        async with async_session_maker() as local_session:
            await _delete_within_session(local_session)
