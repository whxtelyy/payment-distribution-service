from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.dependencies.auth import get_current_user
from app.core.security import get_password_hash
from app.db.session import get_db
from app.main import app
from app.models.user import User

override_get_db = AsyncMock()


@pytest_asyncio.fixture
async def mock_refresh():
    """
    Имитирует поведение метода session.refresh() в SQLAlchemy.
 
    Заполняет объект базовыми атрибутами (id, created_at, balance) после
    создания записи в мок-базе, чтобы избежать ошибок при обращении к полям.
    """
    async def _refresh(obj):
        if hasattr(obj, "id"):
            obj.id = 1
        if hasattr(obj, "created_at"):
            obj.created_at = datetime.now()
        if hasattr(obj, "is_active"):
            obj.is_active = True
        if hasattr(obj, "balance"):
            obj.balance = Decimal(0.00)

    override_get_db.refresh.side_effect = _refresh
    return _refresh


async def get_mock():
    """
    Yield-оператор для подмены сессии БД в тестах.
    Использует AsyncMock() для перехвата вызовов к базе данных.
    """
    yield override_get_db


async def get_user():
    """
    Создает объект тестового пользователя для обхода аутентификации.
    Пароль по умолчанию: '12345'.
    """
    pw = get_password_hash("12345")
    return User(
        id=1,
        username="sava123",
        email="whxtelyy@mail.ru",
        hashed_password=pw,
        is_active=True,
        created_at=datetime.now(),
    )


@pytest_asyncio.fixture
async def client_test():
    """
    Создает ассинхронный тестовый клиент для API.

    Особенности:
    1) Dependency Injection: заменяет реальную БД на мок-объект.
    2) Auth: подменяет получение текущего пользователя на тестовый экземпляр.
    3) Cleanup: автоматически очищает dependency_overrides после завершения теста.
    """
    app.dependency_overrides[get_db] = get_mock
    app.dependency_overrides[get_current_user] = get_user
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.clear()
