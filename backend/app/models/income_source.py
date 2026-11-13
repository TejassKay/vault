from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class IncomeSource(Base):
    __tablename__ = "income_sources"

    income_source_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    frequency: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # monthly, weekly, yearly, one_time
    income_type: Mapped[str] = mapped_column(String(10), nullable=False)  # fixed, variable
    expected_day: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1 to 31
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("amount > 0", name="chk_income_source_amount_positive"),
        CheckConstraint(
            "expected_day IS NULL OR (expected_day >= 1 AND expected_day <= 31)",
            name="chk_income_source_expected_day_range",
        ),
        CheckConstraint(
            "frequency IN ('monthly', 'weekly', 'yearly', 'one_time')",
            name="chk_income_source_frequency",
        ),
        CheckConstraint(
            "income_type IN ('fixed', 'variable')",
            name="chk_income_source_type",
        ),
    )

    user = relationship("User", back_populates="income_sources")
