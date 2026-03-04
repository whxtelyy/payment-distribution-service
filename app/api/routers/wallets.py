from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.wallet import Wallet
from app.schemas.wallet import WalletCreate, WalletRead
from app.services.wallet import create_wallet, get_wallet_by_id

router = APIRouter(prefix="/wallets", tags=["wallets"])


@router.post("/", response_model=WalletRead)
async def create(
    wallet: WalletCreate, user_id: int, db: AsyncSession = Depends(get_db)
) -> Wallet:
    new_wallet = await create_wallet(wallet, user_id, db)
    return new_wallet


@router.get("/{wallet_id}", response_model=WalletRead)
async def get_balance(wallet_id: int, db: AsyncSession = Depends(get_db)) -> Wallet:
    wallet = await get_wallet_by_id(wallet_id, db)
    if wallet is not None:
        return wallet
    else:
        raise HTTPException(status_code=404, detail="No such wallet found")
