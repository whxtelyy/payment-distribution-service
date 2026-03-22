from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.transaction import TransactionStatus
from app.models.wallet import WalletCurrency


class TransactionBase(BaseModel):
    receiver_wallet_id: int
    amount: Decimal = Field(gt=0.01, decimal_places=2)
    currency: WalletCurrency


class TransactionCreate(TransactionBase):
    sender_wallet_id: int
    idempotency_key: UUID | str | None = None
    pass


class TransactionRead(TransactionBase):
    id: int
    status: TransactionStatus
    idempotency_key: UUID | str | None = None
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)
