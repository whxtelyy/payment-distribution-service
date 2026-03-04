from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash


async def create_user(user_in: UserCreate, db: AsyncSession) -> User:
    user_data = user_in.model_dump()
    plain_pass = user_data.pop("password")
    user_data["hashed_password"] = get_password_hash(plain_pass)
    user = User(**user_data)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_user_by_email(email: str, db: AsyncSession) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()
