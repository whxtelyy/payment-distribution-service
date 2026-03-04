from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.transaction import TransactionStatus


class TransactionBase(BaseModel):
    receiver_wallet_id: int
    amount: Decimal
    

class TransactionCreate(TransactionBase):
    pass


class TransactionRead(TransactionBase):
    id: int
    sender_wallet_id: int
    status: TransactionStatus
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)
