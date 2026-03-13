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
    result_conn = await redis.set(f"lock:txn:{transaction_id}", "locked", nx=True, ex=300)
    if result_conn is False:
        return
    else:
        async with AsyncSessionLocal() as session:
            db_result = await session.execute(
                select(Transaction).where(Transaction.id == transaction_id)
            )
            transaction = db_result.scalar_one_or_none()
            if transaction:
                logger.info(
                    f"На кошелек ID = {transaction.receiver_wallet_id} было отправлено "
                    f"{transaction.amount} {transaction.currency.name} "
                    f"с кошелька ID = {transaction.sender_wallet_id}"
                )
            else:
                logger.warning(f"Транзакция {transaction_id} не найдена в базе")
