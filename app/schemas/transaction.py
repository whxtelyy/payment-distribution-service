from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.transaction import TransactionStatus
from app.models.wallet import WalletCurrency


class TransactionBase(BaseModel):
    receiver_wallet_id: int
    amount: Decimal = Field(gt=0.01)


class TransactionCreate(TransactionBase):
    sender_wallet_id: int
    pass


class TransactionRead(TransactionBase):
    id: int
    status: TransactionStatus
    currency: WalletCurrency
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)
