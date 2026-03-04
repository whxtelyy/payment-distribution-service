from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int
    balance: Decimal
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
