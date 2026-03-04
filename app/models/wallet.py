import enum
from datetime import datetime
from decimal import Decimal


from sqlalchemy import Numeric, func, ForeignKey, Enum as EnumSQL
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WalletCurrency(enum.Enum):
    RUB = "rub"
    USD = "usd"
    EUR = "eur"

class Wallet(Base):
    __tablename__ = "wallets"
    id: Mapped[int] = mapped_column(nullable=False, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    balance: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    currency: Mapped[WalletCurrency] = mapped_column(EnumSQL(WalletCurrency), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
