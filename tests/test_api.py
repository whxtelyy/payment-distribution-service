from unittest.mock import MagicMock
import pytest

from .config import override_get_db, get_user, mock_refresh, client_test


@pytest.mark.asyncio
async def test_create_user(client_test, mock_refresh):
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
