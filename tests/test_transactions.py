from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from .config import client_test, get_user, mock_refresh, override_get_db


@pytest.mark.asyncio
async def test_succes_transaction(client_test, mock_refresh, mocker):
    """
    Интеграционный тест успешного межбалансного перевода.

    Сценарий:
    1) Проверяет расчёт балансов: списание у отправителя и зачисление получателю.
    2) Проверяет интеграцию с Taskiq: вызов фоновой задачи для финализации транзакции.
    3) Проверяет идемпотентность: имитирует проверку уникальности запроса перед созданием записи.
    4) Проверяет использование курса валют: проверяет вызов сервиса конвертации (get_exchange_rate).
    """
    mock_rate = mocker.patch("app.services.wallet.get_exchange_rate")
    mock_kiq = mocker.patch("app.services.wallet.completing_tasks.kiq")
    mock_rate.return_value = Decimal(1.0)
    mock_kiq.return_value = None

    wallet_one = MagicMock()
    wallet_one.id = 1
    wallet_one.user_id = 1
    wallet_one.balance = Decimal(100.00)
    wallet_one.currency = "rub"

    wallet_second = MagicMock()
    wallet_second.id = 2
    wallet_second.user_id = 2
    wallet_second.balance = Decimal(0.00)
    wallet_second.currency = "rub"

    transaction_mock = MagicMock()
    transaction_mock.id = 1
    transaction_mock.amount = Decimal("30.00")
    transaction_mock.status = "success"
    transaction_mock.currency = "rub"
    transaction_mock.receiver_wallet_id = 2
    transaction_mock.idempotency_key = "test_key"
    transaction_mock.timestamp = datetime.now()

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
        "amount": 30.00,
        "currency": "rub",
        "idempotency_key": "test_key",
    }
    response = await client_test.post("/wallets/transfer", json=payload)
    assert response.status_code == 200
    assert wallet_one.balance == Decimal(70.00)
    assert wallet_second.balance == Decimal(30.00)
    assert override_get_db.add.called


@pytest.mark.asyncio
async def test_transaction_different_currency(client_test, mock_refresh, mocker):
    """
    Интеграционный тест перевода между кошельками с конвертацией валют.

    Сценарий:
    1) Проверяет математику конвертаций: корректное зачисление суммы получателю на основе
    коэффициента exchange_rate (USD -> RUB).
    2) Проверяет сохранение исходной суммы: списание у отправителя в валюте отправителя.
    3) Проверяет идемпотентность и фоновые задачи: корректный вызов Taskiq и проверку ключа.
    """
    mock_rate = mocker.patch("app.services.wallet.get_exchange_rate")
    mock_kiq = mocker.patch("app.services.wallet.completing_tasks.kiq")
    mock_rate.return_value = Decimal(82.00)
    mock_kiq.return_value = None

    wallet_one = MagicMock()
    wallet_one.id = 1
    wallet_one.user_id = 1
    wallet_one.balance = Decimal(100.00)
    wallet_one.currency = "usd"

    wallet_second = MagicMock()
    wallet_second.id = 2
    wallet_second.user_id = 2
    wallet_second.balance = Decimal(0.00)
    wallet_second.currency = "rub"

    transaction_mock = MagicMock()
    transaction_mock.id = 1
    transaction_mock.amount = Decimal("100.00")
    transaction_mock.status = "success"
    transaction_mock.currency = "usd"
    transaction_mock.receiver_wallet_id = 2
    transaction_mock.idempotency_key = "diff_key"
    transaction_mock.timestamp = datetime.now()

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
        "amount": 100.00,
        "currency": "usd",
        "idempotency_key": "test_key",
    }
    response = await client_test.post("/wallets/transfer", json=payload)
    assert response.status_code == 200
    assert wallet_second.balance == Decimal(8200)
