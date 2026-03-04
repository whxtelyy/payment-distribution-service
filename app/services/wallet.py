from sqlalchemy import select
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
