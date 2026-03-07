from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestFormStrict
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.user import get_user_by_email
from app.core.security import verify_password, token_generation

router = APIRouter(prefix="/login", tags=["login"])


@router.post("/")
async def login(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestFormStrict = Depends(),
):
    db_user = await get_user_by_email(form_data.username, db)
    if db_user is None:
        raise HTTPException(status_code=401, detail="Incorrect login or password")
    else:
        if verify_password(form_data.password, db_user.hashed_password) is False:
            raise HTTPException(status_code=401, detail="Incorrect login or password")
        else:
            access_token = token_generation(db_user.id)
            return {"access_token": access_token, "token_type": "bearer"}
