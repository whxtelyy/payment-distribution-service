from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.dependencies.auth import get_current_user
from app.main import app
from app.tasks import completing_tasks

from .config import client_test, get_user, mock_refresh, override_get_db


@pytest.mark.asyncio
async def test_duplicate_currency(client_test):
    override_get_db.reset_mock()
    override_get_db.add = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = MagicMock()
    override_get_db.execute.return_value = mock_result

    wallet = {"currency": "rub"}
    response = await client_test.post("/wallets/", json=wallet)
    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Wallet with this currency already exists for the user"
    )


@pytest.mark.asyncio
async def test_error_invalid_currency(client_test):
    override_get_db.reset_mock()
    override_get_db.add = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = MagicMock()
    override_get_db.execute.return_value = mock_result

    wallet = {"currency": "ton"}
    response = await client_test.post("/wallets/", json=wallet)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_duplicate_user(client_test):
    override_get_db.reset_mock()
    override_get_db.add = MagicMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = MagicMock()
    override_get_db.execute.return_value = mock_result

    user = {"username": "sava123", "email": "whxtelyy@mail.com", "password": "12345"}
    response = await client_test.post("/users/", json=user)
    assert response.status_code == 400
    assert response.json()["detail"] == "User already exists"


@pytest.mark.asyncio
async def test_unauthorized_create_wallet(client_test):
    override_get_db.reset_mock()
    app.dependency_overrides.pop(get_current_user, None)
    override_get_db.add = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = MagicMock()
    override_get_db.execute.return_value = mock_result

    wallet = {"currency": "rub"}
    response = await client_test.post("/wallets/", json=wallet)
    assert response.status_code == 401

    app.dependency_overrides[get_current_user] = get_user


@pytest.mark.asyncio
async def test_insufficient_funds(client_test, mock_refresh, mocker):
    mock_rate = mocker.patch("app.services.wallet.get_exchange_rate")
    mock_kiq = mocker.patch("app.services.wallet.completing_tasks.kiq")
    mock_rate.return_value = Decimal(1.00)
    mock_kiq.return_value = None

    wallet_one = MagicMock()
    wallet_one.id = 1
    wallet_one.user_id = 1
    wallet_one.balance = Decimal(10.00)
    wallet_one.currency = "rub"

    wallet_second = MagicMock()
    wallet_second.id = 2
    wallet_second.user_id = 2
    wallet_second.balance = Decimal(30.00)
    wallet_second.currency = "rub"

    res_idempotency = MagicMock()
    res_idempotency.scalar_one_or_none.return_value = None

    res1 = MagicMock()
    res1.scalar_one_or_none.return_value = wallet_one

    res2 = MagicMock()
    res2.scalar_one_or_none.return_value = wallet_second

    override_get_db.execute.side_effect = [res_idempotency, res1, res2, res1, res2]

    payload = {
        "sender_wallet_id": 1,
        "receiver_wallet_id": 2,
        "amount": 15.00,
        "currency": "rub",
        "idempotency_key": "test_key",
    }
    response = await client_test.post("/wallets/transfer", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient funds"


@pytest.mark.asyncio
async def test_transaction_yourself(client_test, mock_refresh, mocker):
    mock_rate = mocker.patch("app.services.wallet.get_exchange_rate")
    mock_kiq = mocker.patch("app.services.wallet.completing_tasks.kiq")
    mock_rate.return_value = Decimal(1.00)
    mock_kiq.return_value = None

    wallet = MagicMock()
    wallet.id = 1
    wallet.user_id = 1
    wallet.balance = Decimal(100.00)
    wallet.currency = "rub"

    res = MagicMock()
    res.scalar_one_or_none.return_value = wallet

    res_idempotency = MagicMock()
    res_idempotency.scalar_one_or_none.return_value = None

    override_get_db.execute.side_effect = [res_idempotency, res]

    payload = {
        "sender_wallet_id": 1,
        "receiver_wallet_id": 1,
        "amount": 100.00,
        "currency": "rub",
        "idempotency_key": "test_key",
    }
    response = await client_test.post("/wallets/transfer", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "You cannot transfer money to yourself"


@pytest.mark.asyncio
async def test_wallet_not_found(client_test, mock_refresh, mocker):
    mock_rate = mocker.patch("app.services.wallet.get_exchange_rate")
    mock_kiq = mocker.patch("app.services.wallet.completing_tasks.kiq")
    mock_rate.return_value = Decimal(1.00)
    mock_kiq.return_value = None

    wallet_one = MagicMock()
    wallet_one.id = 1
    wallet_one.user_id = 1
    wallet_one.balance = Decimal(100.00)
    wallet_one.currency = "rub"

    wallet_second = MagicMock()
    wallet_second.id = 2
    wallet_second.user_id = 2
    wallet_second.balance = Decimal(30.00)
    wallet_second.currency = "rub"

    res_idempotency = MagicMock()
    res_idempotency.scalar_one_or_none.return_value = None

    res_none = MagicMock()
    res_none.scalar_one_or_none.return_value = None

    res1 = MagicMock()
    res1.scalar_one_or_none.return_value = None

    res2 = MagicMock()
    res2.scalar_one_or_none.return_value = wallet_second

    override_get_db.execute.side_effect = [res_idempotency, res_none, res2]

    payload = {
        "sender_wallet_id": 1,
        "receiver_wallet_id": 2,
        "amount": 100.00,
        "currency": "rub",
        "idempotency_key": "test_key",
    }
    response = await client_test.post("/wallets/transfer", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Wallet not found"


@pytest.mark.asyncio
async def test_error_idempotency(client_test, mock_refresh, mocker):
    mock_rate = mocker.patch("app.services.wallet.get_exchange_rate")
    mock_kiq = mocker.patch("app.services.wallet.completing_tasks.kiq")
    mock_rate.return_value = Decimal(1.00)
    mock_kiq.return_value = None

    existing_transaction = MagicMock()
    existing_transaction.status = "success"
    existing_transaction.amount = Decimal("30.00")
    existing_transaction.currency = "rub"
    existing_transaction.receiver_wallet_id = 2
    existing_transaction.sender_wallet_id = 1
    existing_transaction.idempotency_key = "test_key"
    existing_transaction.timestamp = datetime.now()

    wallet_one = MagicMock()
    wallet_one.id = 1
    wallet_one.user_id = 1
    wallet_one.balance = Decimal(100.00)
    wallet_one.currency = "rub"

    wallet_second = MagicMock()
    wallet_second.id = 2
    wallet_second.user_id = 2
    wallet_second.balance = Decimal(30.00)
    wallet_second.currency = "rub"

    mock_get_wallet = mocker.patch("app.services.wallet.get_wallet_by_id")
    mock_get_wallet.side_effect = [
        wallet_one,
        wallet_second,
        wallet_one,
        wallet_second,
        wallet_one,
        wallet_second,
        wallet_one,
        wallet_second,
    ]

    res_one = MagicMock()
    res_one.scalar_one_or_none.return_value = None
    res_exists = MagicMock()
    res_exists.scalar_one_or_none.return_value = existing_transaction

    override_get_db.execute.side_effect = [res_one, res_exists]

    payload = {
        "sender_wallet_id": 1,
        "receiver_wallet_id": 2,
        "amount": 30.00,
        "currency": "rub",
        "idempotency_key": "test_key",
    }
    response1 = await client_test.post("/wallets/transfer", json=payload)
    assert response1.status_code == 200
    assert wallet_one.balance == Decimal(70.00)

    response2 = await client_test.post("/wallets/transfer", json=payload)
    assert response2.status_code == 200
    assert wallet_one.balance == Decimal(70.00)


@pytest.mark.asyncio
async def test_worker_lock(mocker):
    mock_redis = AsyncMock()
    mock_redis.set.return_value = False

    mock_session = AsyncMock()
    mock_session_class = MagicMock()
    mock_session_class.return_value.__aenter__.return_value = mock_session
    mocker.patch("app.tasks.AsyncSessionLocal", mock_session_class)

    await completing_tasks(transaction_id=1, redis=mock_redis)
    mock_redis.set.assert_called_once()
    assert not mock_session.execute.called
    assert not mock_session.commit.called
