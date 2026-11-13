from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
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


class Liability(Base):
    __tablename__ = "liabilities"

    liability_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(
        String(15), nullable=False
    )  # home, vehicle, education, personal, credit_card, other
    lender_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    outstanding_principal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    interest_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)  # annual percent
    emi_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    due_day: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 to 31
    remaining_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prepayment_note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(10), nullable=False, default="active"
    )  # active, closed
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("outstanding_principal >= 0", name="chk_liability_principal_non_negative"),
        CheckConstraint("interest_rate >= 0", name="chk_liability_interest_non_negative"),
        CheckConstraint("emi_amount >= 0", name="chk_liability_emi_non_negative"),
        CheckConstraint("due_day >= 1 AND due_day <= 31", name="chk_liability_due_day_range"),
        CheckConstraint(
            "remaining_months IS NULL OR remaining_months >= 0",
            name="chk_liability_remaining_months_non_negative",
        ),
        CheckConstraint(
            "type IN ('home', 'vehicle', 'education', 'personal', 'credit_card', 'other')",
            name="chk_liability_type",
        ),
        CheckConstraint("status IN ('active', 'closed')", name="chk_liability_status"),
    )

    user = relationship("User", back_populates="liabilities")
    reminders = relationship("Reminder", back_populates="liability", cascade="all, delete-orphan")
