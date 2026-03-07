import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import ALGORITHM
from app.db.session import get_db
from app.models.user import User
from app.services.user import get_user_by_id


async def get_current_user(
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="login")),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        decode_token = jwt.decode(token, settings.SECRET_KEY, ALGORITHM)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="The token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        user_id = decode_token.get("sub")
    except KeyError:
        raise HTTPException(status_code=401, detail="User ID not found")
    user_id_int = int(user_id)
    db_user = await get_user_by_id(user_id_int, db)
    if db_user is None:
        raise HTTPException(status_code=401, detail="DB User not found")
    else:
        return db_user
