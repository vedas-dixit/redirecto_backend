from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from models.models import User
from sqlalchemy.ext.asyncio import AsyncSession


async def create_user_if_not_exists(payload: dict, session: AsyncSession) -> User:
    """
    Checks if a user exists by provider_id. If not, creates one using provided payload.
    Returns the existing or newly created user.
    """

    try:
        # Step 1: Check if user exists by provider_id
        stmt = select(User).where(User.id == payload["id"])
        result = await session.execute(stmt)
        user = result.scalars().first()

        if user:
            print("USER FOUNDDDDDDDDDDDD")
            return user  # Return existing user

        # Step 2: Create new user
        new_user = User(
            id=payload.get("id"),
            is_guest=payload.get("is_guest", False),
            email=payload.get("email"),
            name=payload.get("name"),
            avatar_url=payload.get("avatar_url"),
            provider=payload.get("provider"),
            provider_id=payload.get("provider_id"),
        )

        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user

    except SQLAlchemyError as e:
        print(f"Error in create_user_if_not_exists: {str(e)}")
        await session.rollback()
        raise e
