from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wallet import Wallet
from app.schemas.wallet import WalletCreate


async def create_wallet(
    wallet_data: WalletCreate, user_id: int, db: AsyncSession
) -> Wallet:
    wallet = Wallet(**wallet_data.model_dump(), user_id=user_id)
    db.add(wallet)
    await db.commit()
    await db.refresh(wallet)
    return wallet


async def get_wallet_by_id(wallet_id: int, db: AsyncSession) -> Wallet | None:
    result = await db.execute(select(Wallet).where(Wallet.id == wallet_id))
    return result.scalars().first()


async def update_balance(wallet_id: int, amount: Decimal, db: AsyncSession) -> Wallet | None:
    result = await db.execute(
        update(Wallet)
        .values(balance=Wallet.balance + amount)
        .where(Wallet.id == wallet_id)
        .returning(Wallet)
    )
    await db.commit()
    return result.scalar_one_or_none()
