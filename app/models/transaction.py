import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Enum as EnumSQL
from sqlalchemy import ForeignKey, Numeric, func, String, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.wallet import WalletCurrency


class TransactionStatus(enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(nullable=False, primary_key=True, index=True)
    sender_wallet_id: Mapped[int] = mapped_column(
        ForeignKey("wallets.id"), nullable=False, index=True
    )
    receiver_wallet_id: Mapped[int] = mapped_column(
        ForeignKey("wallets.id"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), CheckConstraint("amount > 0"), nullable=False
    )
    currency: Mapped[WalletCurrency] = mapped_column(
        EnumSQL(WalletCurrency), nullable=False
    )
    status: Mapped[TransactionStatus] = mapped_column(
        EnumSQL(TransactionStatus), nullable=False
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=True, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False, index=True)
