from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import bcrypt

from models.models import URL
from database.db import get_session
from schemas.dashboard import VerifyPasswordRequest, VerifyPasswordResponse  # adjust paths

router = APIRouter()

@router.post("/verify-password")
async def verify_password(
    payload: VerifyPasswordRequest,
    session: AsyncSession = Depends(get_session)
):
    stmt = select(URL).where(URL.short_code == payload.short_code)
    result = await session.execute(stmt)
    url = result.scalars().first()

    if not url:
        raise HTTPException(status_code=404, detail="Short URL not found.")

    if not url.is_protected or not url.password_hash:
        raise HTTPException(status_code=400, detail="URL is not protected or has no password.")

    # Verify the password
    if not bcrypt.checkpw(payload.password.encode('utf-8'), url.password_hash.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Incorrect password.")

    return {"destination": url.destination}
