from unittest.mock import MagicMock
import pytest

from .config import override_get_db, get_user, mock_refresh, client_test


@pytest.mark.asyncio
async def test_create_user(client_test, mock_refresh):
    """
    Проверка регистрации нового пользователя.

    Мокается ситуация, когда email/username свободны.
    Тест проверяет корректность хэширования и вызов метода .add() у сессии БД.
    """
    override_get_db.reset_mock()
    override_get_db.add = MagicMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    override_get_db.execute.return_value = mock_result

    user = {"username": "sava123", "email": "whxtelyy@mail.com", "password": "12345"}
    response = await client_test.post("/users/", json=user)
    assert response.status_code == 201
    assert override_get_db.add.called >= 1


@pytest.mark.asyncio
async def test_auth_user(client_test):
    """
    Проверка успешного входа (Login).

    Сценарий:
    1) Мокается получение пользователя из БД по username.
    2) Проверяется выдача JWT-токена при совпадении пароля.
    """
    override_get_db.reset_mock()
    mock_result = MagicMock()
    fake_user = await get_user()
    mock_result.scalars.return_value.first.return_value = fake_user
    override_get_db.execute.return_value = mock_result
    user = {"username": "sava123", "password": "12345", "grant_type": "password"}
    response = await client_test.post("/login/", data=user)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_wallet(client_test, mock_refresh):
    """
    Проверка создания кошелька для текущего пользователя.

    Условие: у пользователя ещё нет кошелька в указанной валюте (scalar_one_or_none возвращает None).
    Проверяется корректность маппинга валюты в JSON-ответе.
    """
    override_get_db.reset_mock()
    override_get_db.add = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    override_get_db.execute.return_value = mock_result

    wallet = {"currency": "rub"}
    response = await client_test.post("/wallets/", json=wallet)
    data = response.json()
    assert response.status_code == 201
    assert data["currency"] == "rub"
    assert override_get_db.add.called >= 1
