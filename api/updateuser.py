from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.models import User
from database.db import get_session
from schemas.dashboard import UpdateUserRequest, UpdateUserResponse
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter()

@router.patch("/user/update", response_model=UpdateUserResponse)
async def update_user_details(
    request: UpdateUserRequest,
    session: AsyncSession = Depends(get_session),
):
    try:
        # 1. Fetch user
        stmt = select(User).where(User.id == request.user_id)
        result = await session.execute(stmt)
        user = result.scalars().first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # 2. Update fields if provided
        if request.name:
            user.name = request.name
        if request.email:
            user.email = request.email

        await session.commit()
        await session.refresh(user)

        return UpdateUserResponse(
            user_id=user.id,
            name=user.name,
            email=user.email,
            message="User details updated successfully"
        )

    except SQLAlchemyError as e:
        await session.rollback()
        print(f"DB Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")

    except Exception as e:
        print(f"Unexpected Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
