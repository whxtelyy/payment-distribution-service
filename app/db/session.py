import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@postgres_db_payment_service:5432/{settings.POSTGRES_DB}",
)

engine = create_async_engine(DATABASE_URL, echo=False)

AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Генератор асинхронных сессий базы данных.

    Особенности:
    1) Использует как FastAPI Dependency для внедрения сессии в эндпоинты.
    2) Гарантирует автоматическое закрытие сессии после завершение обработки запроса.
    3) Использует контекстный менеджер для обеспечения безопасности транзакций.
    """
    async with AsyncSessionLocal() as session:
        yield session
