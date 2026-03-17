from unittest.mock import AsyncMock, MagicMock

import pytest

from app.tasks import completing_tasks

from .config import client_test, get_user, mock_refresh, override_get_db


@pytest.mark.asyncio
async def test_happy_path(mocker):
    mock_redis = AsyncMock()
    mock_redis.set.return_value = True

    tx_mock = MagicMock()
    tx_mock.id = 1
    tx_mock.receiver_wallet_id = 10
    tx_mock.sender_wallet_id = 5
    tx_mock.amount = 100.0
    tx_mock.currency.name = "RUB"
    tx_mock.status = "pending"

    mock_session = AsyncMock()
    mock_db_result = MagicMock()
    mock_db_result.scalar_one_or_none.return_value = tx_mock
    mock_session.execute.return_value = mock_db_result

    mock_session_class = MagicMock()
    mock_session_class.return_value.__aenter__.return_value = mock_session
    mocker.patch("app.tasks.AsyncSessionLocal", mock_session_class)

    await completing_tasks(transaction_id=1, redis=mock_redis)
    mock_redis.set.assert_called_once_with("lock:txn:1", "locked", nx=True, ex=300)
    assert tx_mock.status == "success"
    assert mock_session.commit.called
