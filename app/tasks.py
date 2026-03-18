import logging

import redis.asyncio
from sqlalchemy import select
from taskiq import TaskiqDepends

from app.core.tqk import broker, get_redis_conn
from app.db.session import AsyncSessionLocal
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@broker.task
async def completing_tasks(
    transaction_id: int, redis: redis.asyncio.Redis = TaskiqDepends(get_redis_conn)
) -> None:
    """
    Фоновая задача для подтверждения и финализации транзакции.

    Сценарий:
    1) Распределенная блокировка: использование REDIS SET NX гарантирует,
    что задачу возьмёт в работу только один воркер. Это исключает повторное списание средств.
    2) TTL Блокировки: установлен лимит в 300 секунд (ex=300), чтобы в случае падения воркера
    задача не заблокировалась навечно.
    3) Атомарность: Статус транзакции обновляется на 'success' только после успешного выполнения
    бизнес-логики и коммита в БД.
    4) Очистка: Блокировка снимается в блоке finally, позволяя системе обрабатывать следующие
    задачи для этого ID (если потребуется).
    """
    lock_key = f"lock:txn:{transaction_id}"
    result_conn = await redis.set(lock_key, "locked", nx=True, ex=300)
    if result_conn is False:
        logger.info(
            f"Задача для транзакции {transaction_id} уже выполняется другим воркером"
        )
        return
    try:
        async with AsyncSessionLocal() as session:
            db_result = await session.execute(
                select(Transaction).where(Transaction.id == transaction_id)
            )
            transaction = db_result.scalar_one_or_none()
            if transaction:
                transaction.status = "success"
                logger.info(
                    f"На кошелек ID = {transaction.receiver_wallet_id} было отправлено "
                    f"{transaction.amount} {transaction.currency.name} "
                    f"с кошелька ID = {transaction.sender_wallet_id}"
                )
                await session.commit()
            else:
                logger.warning(f"Транзакция {transaction_id} не найдена в базе")
    except Exception as error:
        logger.error((f"Ошибка при обработке транзакции {transaction_id}: {error}"))
        raise
    finally:
        await redis.delete(lock_key)
        logger.info(f"Блокировка {lock_key} снята")
