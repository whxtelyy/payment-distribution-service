from passlib.context import CryptContext

import jwt
from datetime import datetime, timezone, timedelta

from .config import settings

ALGORITHM = "HS256"

hashed = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return hashed.hash(password)

def token_generation(user_id: str) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)

def verify_password(user_password: str, hash_password: str) -> bool:
    return hashed.verify(user_password, hash_password)
