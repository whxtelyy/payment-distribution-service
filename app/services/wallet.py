from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select, or_, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.tasks import completing_tasks
from app.core.external.currency_api import get_exchange_rate
from app.models.transaction import Transaction, TransactionStatus
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


async def get_wallet_by_id(
    wallet_id: int, db: AsyncSession, for_update: bool
) -> Wallet | None:
    result = select(Wallet).where(Wallet.id == wallet_id)
    if for_update is True:
        result = result.with_for_update()
    result = await db.execute(result)
    return result.scalar_one_or_none()


async def get_wallet_by_user_id(
    user_id: int, currency: str, db: AsyncSession, for_update: bool
) -> Wallet | None:
    result = select(Wallet).where(
        and_(Wallet.user_id == user_id, Wallet.currency == currency)
    )
    if for_update is True:
        result = result.with_for_update()
    result = await db.execute(result)
    return result.scalar_one_or_none()


async def update_balance(
    user_id: int, currency: str, amount: Decimal, db: AsyncSession
) -> Wallet | None:
    wallet = await get_wallet_by_user_id(user_id, currency, db, False)
    if wallet is None:
        wallet = Wallet(user_id=user_id, balance=amount, currency=currency)
    else:
        wallet.balance += amount
    db.add(wallet)
    await db.commit()
    await db.refresh(wallet)
    return wallet


async def make_transfer(
    current_user_id: int,
    sender_wallet_id: int,
    receiver_wallet_id: int,
    amount: Decimal,
    db: AsyncSession,
    idempotency_key: str | None = None,
) -> Transaction:
    try:
        if sender_wallet_id == receiver_wallet_id:
            raise ValueError("You cannot transfer money to yourself")
        sender_wallet = await get_wallet_by_id(sender_wallet_id, db, False)
        if sender_wallet.user_id != current_user_id:
            raise ValueError("Access denied")
        receiver_wallet = await get_wallet_by_id(receiver_wallet_id, db, False)
        if not sender_wallet or not receiver_wallet:
            raise ValueError("One of the wallets does not exist")
        if sender_wallet.balance < amount:
            raise ValueError("Insufficient funds")
        else:
            try:
                rate = await get_exchange_rate(
                    sender_wallet.currency, receiver_wallet.currency
                )
            except ValueError:
                raise ValueError("Currency service unavailable, try later")
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
        receiver_wallet.balance = receiver_wallet.balance.quantize(Decimal("0.01"))
        new_transaction = Transaction(
            sender_wallet_id=sender_wallet.id,
            receiver_wallet_id=receiver_wallet.id,
            amount=amount,
            currency=sender_wallet.currency,
            status=TransactionStatus.SUCCESS,
            idempotency_key=idempotency_key,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(new_transaction)
        try:
            await db.commit()
            await db.refresh(new_transaction)
            await completing_tasks.kiq(transaction_id=int(new_transaction.id))
            return new_transaction
        except IntegrityError:
            await db.rollback()
            result = await db.execute(
                select(Transaction).where(
                    Transaction.idempotency_key == idempotency_key
                )
            )
            result = result.scalar_one_or_none()
            if result is None:
                raise IntegrityError(
                    "There was no idempotency key or nothing was found"
                )
            await completing_tasks.kiq(transaction_id=int(result.id))
            return result
    except Exception as error:
        await db.rollback()
        raise error


async def get_user_transactions(
    wallet_ids: list[int], limit_tr: int | None, skip: int | None, db: AsyncSession
) -> list[Transaction]:
    result = await db.execute(
        select(Transaction)
        .where(
        or_(
            Transaction.sender_wallet_id.in_(wallet_ids),
            Transaction.receiver_wallet_id.in_(wallet_ids),
            )
        )
        .order_by(Transaction.timestamp.desc())
        .limit(limit_tr)
        .offset(skip)
    )
    return list(result.scalars().all())


async def get_user_all_wallets(
    user_id: int, db: AsyncSession
) -> list[Wallet]:
    result = await db.execute(
        select(Wallet)
        .where(
            Wallet.user_id == user_id
        )
        .order_by(Wallet.currency.asc())
    )
    return list(result.scalars().all())
