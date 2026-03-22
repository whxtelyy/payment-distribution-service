from passlib.context import CryptContext

import jwt
from datetime import datetime, timezone, timedelta

from .config import settings

ALGORITHM = "HS256"

hashed = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Возвращает хэш пароля с использованием алгоритма bcrypt."""
    return hashed.hash(password)

def token_generation(user_id: str) -> str:
    """
    Генерирует JWT-токен доступа для аутентификации пользователя.
    
    Особенности:
    1) sub (subject): Идентификатор пользователя.
    2) exp (expiration time): Время жизни токена - 1 час с момента выпуска.
    
    Использует алгоритм HS256 и секретный ключ из конфигурации приложения.
    """
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)

def verify_password(user_password: str, hash_password: str) -> bool:
    """
    Сравнивает пароль пользователя с его хэшем.
    Устойчив к атакам по времени благодаря встроенным механизмам passlib.
    """
    return hashed.verify(user_password, hash_password)
