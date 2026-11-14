from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Holding(Base):
    __tablename__ = "holdings"

    holding_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # bank_savings, fixed_deposit, mutual_fund, stocks, bonds, gold, retirement, other
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    current_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    liquidity: Mapped[str] = mapped_column(
        String(15), nullable=False
    )  # liquid, semi_liquid, locked
    is_emergency_reserve: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    source: Mapped[str] = mapped_column(String(10), nullable=False, default="manual")

    __table_args__ = (
        CheckConstraint("current_value >= 0", name="chk_holding_value_non_negative"),
        CheckConstraint(
            "type IN ('bank_savings', 'fixed_deposit', 'mutual_fund', 'stocks', 'bonds', 'gold', 'retirement', 'other')",
            name="chk_holding_type",
        ),
        CheckConstraint(
            "liquidity IN ('liquid', 'semi_liquid', 'locked')", name="chk_holding_liquidity"
        ),
    )

    user = relationship("User", back_populates="holdings")
