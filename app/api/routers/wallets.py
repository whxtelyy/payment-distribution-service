from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.wallet import Wallet
from app.schemas.wallet import WalletCreate, WalletRead
from app.schemas.transaction import TransactionBase
from app.services.wallet import create_wallet, update_balance

router = APIRouter(prefix="/wallets", tags=["wallets"])


@router.post("/", response_model=WalletRead)
async def create(
    wallet: WalletCreate, user_id: int, db: AsyncSession = Depends(get_db)
) -> Wallet:
    new_wallet = await create_wallet(wallet, user_id, db)
    return new_wallet


@router.get("/{wallet_id}", response_model=WalletRead)
async def get_balance(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> Wallet:
    result = await db.execute(select(Wallet).where(Wallet.user_id == current_user.id))
    result_wallet = result.scalars().first()

    if result_wallet is not None:
        if result_wallet.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not your wallet")
        else:
            return result_wallet
    else:
        raise HTTPException(status_code=404, detail="No such wallet found")


@router.patch("/{wallet_id}/deposit", response_model=WalletRead)
async def update_balance_wallet(
    deposit_data: TransactionBase,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Wallet:
    result = await db.execute(select(Wallet).where(Wallet.user_id == current_user.id))
    wallet = result.scalars().first()
    if wallet is None:
        return await create_wallet(
            WalletCreate(balance=0, currency="rub"),
            current_user.id, db
        )
    else:
        return await update_balance(wallet.id, deposit_data.amount, db)
