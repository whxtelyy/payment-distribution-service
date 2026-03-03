from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings


engine = create_async_engine(
    f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@localhost:{settings.POSTGRES_DB_PORT}/{settings.POSTGRES_DB}",
    echo=True,
)

AsyncSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, expire_on_commit=False, bind=engine
)
