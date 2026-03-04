from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.wallet import WalletCurrency


class WalletBase(BaseModel):
    currency: WalletCurrency


class WalletCreate(WalletBase):
    pass


class WalletRead(WalletBase):
    id: int
    user_id: int
    balance: Decimal
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
