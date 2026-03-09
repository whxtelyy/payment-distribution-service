from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionBase, TransactionCreate, TransactionRead
from app.models.user import User
from app.models.wallet import Wallet
from app.schemas.wallet import WalletCreate, WalletRead, WalletCurrency
from app.services.wallet import (
    create_wallet,
    update_balance,
    get_wallet_by_user_id,
    make_transfer,
    get_user_transactions,
    get_wallet_by_id,
)

router = APIRouter(prefix="/wallets", tags=["wallets"])


@router.post("/", response_model=WalletRead, status_code=201)
async def create(
    wallet: WalletCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Wallet:
    if (
        await get_wallet_by_user_id(current_user.id, wallet.currency, db, False)
        is not None
    ):
        raise HTTPException(
            status_code=400,
            detail="Wallet with this currency already exists for the user",
        )
    new_wallet = await create_wallet(wallet, current_user.id, db)
    return new_wallet


@router.get("/me", response_model=WalletRead, status_code=200)
async def get_balance(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> Wallet:
    result_wallet = await get_wallet_by_user_id(
        current_user.id, WalletCurrency.RUB, db, False
    )

    if result_wallet is None:
        raise HTTPException(status_code=404, detail="No such wallet found")
    return result_wallet


@router.patch("/{wallet_id}/deposit", response_model=WalletRead, status_code=200)
async def update_balance_wallet(
    deposit_data: TransactionBase,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Wallet:
    if current_user.email != "isaev_saveliy_d@mail.ru":
        raise HTTPException(status_code=403, detail="This user is not admin")
    wallet = await get_wallet_by_user_id(current_user.id, WalletCurrency.RUB, db, False)
    if wallet is None:
        return await create_wallet(
            WalletCreate(balance=deposit_data.amount, currency="rub"),
            current_user.id,
            db,
        )
    else:
        return await update_balance(wallet.id, deposit_data.amount, db)


@router.post("/transfer", response_model=TransactionRead, status_code=200)
async def make_transfer_wallet(
    transfer_data: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Transaction:
    try:
        transfer_result = await make_transfer(
            current_user.id,
            transfer_data.sender_wallet_id,
            transfer_data.receiver_wallet_id,
            transfer_data.amount,
            db,
            transfer_data.idempotency_key,
        )
        return transfer_result
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.get("/transactions", response_model=list[TransactionRead], status_code=200)
async def get_transactions(
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[Transaction]:
    wallet = await get_wallet_by_user_id(current_user.id, WalletCurrency.RUB, db, False)
    if wallet is None:
        return []
    else:
        new_transaction = await get_user_transactions(wallet.id, limit, skip, db)
        return new_transaction
