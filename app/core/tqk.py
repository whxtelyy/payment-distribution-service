from collections.abc import AsyncGenerator

import redis.asyncio
from taskiq_redis import ListQueueBroker, RedisAsyncResultBackend

import app.core.logging_config
from app.core.config import settings

broker = ListQueueBroker(
    url=f"redis://localhost:{settings.REDIS_PORT}/{settings.REDIS_DB}",
)

result_backend = RedisAsyncResultBackend(
    redis_url=f"redis://localhost:{settings.REDIS_PORT}/{settings.REDIS_DB}",
    result_ex_time=1000,
)

broker.with_result_backend(result_backend)


async def get_redis_conn() -> AsyncGenerator[redis.asyncio.Redis | None]:
    async with redis.asyncio.from_url(
        f"redis://localhost:{settings.REDIS_PORT}/{settings.REDIS_DB}"
    ) as connect:
        yield connect
