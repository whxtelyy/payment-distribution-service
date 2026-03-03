from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import func, ForeignKey, Numeric, Enum as EnumSQL
from decimal import Decimal
import enum
from datetime import datetime

from app.db.base import Base


class TransactionStatus(enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(nullable=False, primary_key=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    receiver_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(EnumSQL(TransactionStatus), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)