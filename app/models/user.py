from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Numeric, String, func
from decimal import Decimal
from datetime import datetime


from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(nullable=False, primary_key=True)
    username: Mapped[str] = mapped_column(String(30), nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(10,2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)