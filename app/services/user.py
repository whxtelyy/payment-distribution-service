from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate


async def create_user(user_in: UserCreate, db: AsyncSession) -> User:
    """
    Создает нового пользователя в системе с хэшированием пароля.

    Сценарий:
    1) Трансформация: извлекает данные из схемы и заменяет пароль на хэш (bcrypt).
    2) Персистентность: сохраняет объект User в сессии SQLAlchemy.
    3) Синхронизация: выполняет commit и refresh, чтобы объект содержал
    сгенерированные БД поля (ID, даты).
    """
    user_data = user_in.model_dump()
    plain_pass = user_data.pop("password")
    user_data["hashed_password"] = get_password_hash(plain_pass)
    user = User(**user_data)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_user_by_email(email: str, db: AsyncSession) -> User | None:
    """
    Выполняет поиск пользователя по адресу электронной почты.
    Используется для проверки уникальности при регистрации в процессе аутентификации.
    """
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def get_user_by_id(id: str, db: AsyncSession) -> User | None:
    """
    Выполняет поиск пользователя по уникальному идентефикатору.
    Используется для получения профиля и проверки уникальности при регистрации
    в процессе аутентификации.
    """
    result = await db.execute(select(User).where(User.id == id))
    return result.scalars().first()
