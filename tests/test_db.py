import asyncio
from sqlalchemy import text

from app.db.session import AsyncSessionLocal


async def test_db(command: str):
    async with AsyncSessionLocal() as connection:
        result = await connection.execute(text(command))
        print(f"Ответ базы: {result.scalar()}")


if __name__ == "__main__":
    asyncio.run(test_db("SELECT 1"))
