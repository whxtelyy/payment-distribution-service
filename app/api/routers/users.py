from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import UserCreate, UserRead
from app.models.user import User
from app.services.user import get_user_by_email, create_user
from app.db.session import get_db


router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.post("/", response_model=UserRead)
async def registration(user: UserCreate, db: AsyncSession = Depends(get_db)) -> User:
    if await get_user_by_email(user.email, db) is None:
        new_user = await create_user(user, db)
        return new_user
    else:
        raise HTTPException(status_code=400, detail="User already exists")