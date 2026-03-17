import os
from collections.abc import AsyncGenerator

import redis.asyncio
from taskiq_redis import ListQueueBroker, RedisAsyncResultBackend

import app.core.logging_config
from app.core.config import settings

REDIS_URL = os.getenv("REDIS_URL", f"redis://redis_payment_service:6379/0")

broker = ListQueueBroker(url=REDIS_URL)

result_backend = RedisAsyncResultBackend(
    redis_url=REDIS_URL,
    result_ex_time=1000,
)

broker.with_result_backend(result_backend)


async def get_redis_conn() -> AsyncGenerator[redis.asyncio.Redis | None]:
    async with redis.asyncio.from_url(REDIS_URL) as connect:
        yield connect
