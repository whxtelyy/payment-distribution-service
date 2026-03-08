from decimal import Decimal

from sqlalchemy import select, update, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.external.currency_api import get_exchange_rate
from app.models.transaction import Transaction, TransactionStatus
from app.models.wallet import Wallet
from app.schemas.wallet import WalletCreate


async def create_wallet(
    wallet_data: WalletCreate, user_id: int, db: AsyncSession
) -> Wallet:
    wallet = Wallet(**wallet_data.model_dump(), user_id=user_id)
    db.add(wallet)
    return wallet


async def get_wallet_by_id(wallet_id: int, db: AsyncSession, for_update: bool) -> Wallet | None:
    result = select(Wallet).where(Wallet.id == wallet_id)
    if for_update is True:
        result = result.with_for_update()
    result = await db.execute(result)
    return result.scalar_one_or_none()


async def get_wallet_by_user_id(
    user_id: int, currency: str, db: AsyncSession, for_update: bool
) -> Wallet | None:
    result = select(Wallet).where(and_(Wallet.user_id == user_id, Wallet.currency == currency))
    if for_update is True:
        result = result.with_for_update()
    result = await db.execute(result)
    return result.scalar_one_or_none()


async def update_balance(
    wallet_id: int, amount: Decimal, db: AsyncSession
) -> Wallet | None:
    result = await db.execute(
        update(Wallet)
        .values(balance=Wallet.balance + amount)
        .where(Wallet.id == wallet_id)
        .returning(Wallet)
    )
    return result.scalar_one_or_none()


async def make_transfer(
    sender_wallet_id: int, receiver_wallet_id: int, amount: Decimal, db: AsyncSession
) -> Transaction:
    try:
        sender_wallet = await get_wallet_by_id(sender_wallet_id, db, False)
        receiver_wallet = await get_wallet_by_id(receiver_wallet_id, db, False)
        if not sender_wallet or not receiver_wallet:
            raise ValueError("One of the wallets does not exist")
        if sender_wallet.balance < amount:
            raise ValueError("Insufficient funds")
        else:
            rate = await get_exchange_rate(sender_wallet.currency, receiver_wallet.currency)
            if sender_wallet_id < receiver_wallet_id:
                sender_wallet = await get_wallet_by_id(sender_wallet_id, db, True)
                if sender_wallet.balance < amount:
                    raise ValueError("Insufficient funds")
                receiver_wallet = await get_wallet_by_id(receiver_wallet_id, db, True)
            else:
                receiver_wallet = await get_wallet_by_id(receiver_wallet_id, db, True)
                sender_wallet = await get_wallet_by_id(sender_wallet_id, db, True)
                if sender_wallet.balance < amount:
                    raise ValueError("Insufficient funds")
        
        sender_wallet.balance -= amount
        receiver_wallet.balance += amount * rate
        new_transaction = Transaction(
            sender_wallet_id=sender_wallet.id,
            receiver_wallet_id=receiver_wallet.id,
            amount=amount,
            currency=sender_wallet.currency,
            status=TransactionStatus.SUCCESS,
        )
        db.add(new_transaction)
        await db.commit()
        await db.refresh(new_transaction)
        return new_transaction
    except Exception as error:
        await db.rollback()
        raise error
    

async def get_user_transactions(wallet_id: int, limit_tr: int, skip: int, db: AsyncSession) -> list[Transaction]:
    result = await db.execute(
        select(Transaction)
        .where(
            or_(
                wallet_id == Transaction.sender_wallet_id,
                wallet_id == Transaction.receiver_wallet_id,
            )
        )
        .order_by(Transaction.timestamp.desc()).limit(limit_tr).offset(skip)
    )
    return result.scalars().all()
