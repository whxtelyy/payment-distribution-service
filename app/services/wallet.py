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
    """
    Создает нового кошелька в системе.

    Сценарий:
    1) Трансформация: извлекает данные из схемы и заменяет user_id на уникальный
    идентификатор пользователя.
    2) Персистентность: сохраняет объект Wallet в сессии SQLAlchemy.
    3) Синхронизация: выполняет commit и refresh, чтобы объект содержал
    сгенерированные БД поля (user_id).
    """
    wallet = Wallet(**wallet_data.model_dump(), user_id=user_id)
    db.add(wallet)
    await db.commit()
    await db.refresh(wallet)
    return wallet


async def get_wallet_by_id(
    wallet_id: int, db: AsyncSession, for_update: bool
) -> Wallet | None:
    """
    Выполняет поиск кошелька по уникальному идентификатору.
    Используется для проверки уникальности при создании кошелька.
    """
    result = select(Wallet).where(Wallet.id == wallet_id)
    if for_update is True:
        result = result.with_for_update()
    result = await db.execute(result)
    return result.scalar_one_or_none()


async def get_wallet_by_user_id(
    user_id: int, currency: str, db: AsyncSession, for_update: bool
) -> Wallet | None:
    """
    Выполняет поиск кошелька по уникальному идентификатору владельца.
    Используется для проверки уникальности при создании кошелька..
    """
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
    """
    Обновляет баланс кошелька.

    Сценарий:
    1) Проверка на существование кошелька.
    2) Добавляет к балансу кошелька сумму обновления.
    3) Персистентность: сохраняет объект Wallet в сессии SQLAlchemy.
    4) Синхронизация: выполняет commit и refresh, чтобы объект содержал
    сгенерированные БД поля (user_id, balance, currency).

    Raises:
        ValueError: при попытке обновить баланс несуществующего кошелька.
    """
    wallet = await get_wallet_by_user_id(user_id, currency, db, False)
    if wallet is None:
        raise ValueError("Wallet not found")
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
    """
    Выполняет перевод средств между кошельками с учётом конвертации валют.

    Сценарий:
    1) Идемпотентность: проверка по ключу гарантирует, что повторный запрос
    не приведёт к повторному списанию.
    2) Консистентность: применяется SELECT FOR UPDATE для защиты баланса от
    Race Conditions. Блокировка выполняется строго в порядке возрастания ID,
    что исключает возникновение Deadlocks при встречных переводах.
    3) Точность: сумма зачисления (delta) вычисляется через внешний курс и
    округляется до двух знаков.
    4) Reliability: вызов фоновой задачи Taskiq происходит только после успешного
    коммита.

    Raises:
        ValueError: при недостатке средств, попытке перевода самому себе,
        несовпадении данных по ключю идемпотентности или ошибке сервиса валют.
    """
    if idempotency_key:
        result = await db.execute(
            select(Transaction).where(Transaction.idempotency_key == idempotency_key)
        )
        existing_transaction = result.scalar_one_or_none()
        if existing_transaction:
            return existing_transaction
    try:
        if sender_wallet_id == receiver_wallet_id:
            raise ValueError("You cannot transfer money to yourself")
        sender_wallet = await get_wallet_by_id(sender_wallet_id, db, False)
        if sender_wallet is None:
            raise ValueError("Wallet not found")
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
        delta = (amount * rate).quantize(Decimal("0.01"))
        receiver_wallet.balance += delta
        receiver_wallet.balance = receiver_wallet.balance.quantize(Decimal("0.01"))
        new_transaction = Transaction(
            sender_wallet_id=sender_wallet.id,
            receiver_wallet_id=receiver_wallet.id,
            amount=amount,
            currency=sender_wallet.currency,
            status=TransactionStatus.SUCCESS,
            idempotency_key=idempotency_key,
            timestamp=datetime.now(timezone.utc),
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
            if (
                result.amount.normalize() != amount.normalize()
                or result.receiver_wallet_id != receiver_wallet_id
                or result.sender_wallet_id != sender_wallet_id
            ):
                raise ValueError("Data conflict")
            await completing_tasks.kiq(transaction_id=int(result.id))
            return result
    except Exception as error:
        await db.rollback()
        raise error


async def get_user_transactions(
    wallet_ids: list[int], limit_tr: int | None, skip: int | None, db: AsyncSession
) -> list[Transaction]:
    """
    Возвращает список транзакций с кошельков переданных по уникальному идентификатор пользователей.

    Запрос к БД: ищет транзакции, которые были совершены самим пользователем или
    которые были совершены другим пользователем, но на счёт пользователя. Учитывает
    limit (максимальное количество транзакций на вывод) и offset (кол-во транзакций,
    которые надо пропустить в начале). Вывод от самых новых до самых старых.
    """
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


async def get_user_all_wallets(user_id: int, db: AsyncSession) -> list[Wallet]:
    """
    Возвращает список транзакций со всех кошельков пользователя.

    Запрос к БД: ищет транзакции, которые были совершены самим пользователем
    на всех его кошельках. Вывод производится в алфавитном порядке валют
    ('eur', 'rub', 'usd).
    """
    result = await db.execute(
        select(Wallet).where(Wallet.user_id == user_id).order_by(Wallet.currency.asc())
    )
    return list(result.scalars().all())
