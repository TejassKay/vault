from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Goal(Base):
    __tablename__ = "goals"

    goal_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    target_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    saved_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    target_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    priority: Mapped[str] = mapped_column(
        String(6), nullable=False, default="medium"
    )  # high, medium, low
    liquidity_need: Mapped[str] = mapped_column(String(6), nullable=False, default="medium")
    status: Mapped[str] = mapped_column(
        String(10), nullable=False, default="active"
    )  # active, achieved, paused
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("target_amount > 0", name="chk_goal_target_positive"),
        CheckConstraint("saved_amount >= 0", name="chk_goal_saved_non_negative"),
        CheckConstraint("priority IN ('high', 'medium', 'low')", name="chk_goal_priority"),
        CheckConstraint("status IN ('active', 'achieved', 'paused')", name="chk_goal_status"),
    )

    user = relationship("User", back_populates="goals")
    reminders = relationship("Reminder", back_populates="goal", cascade="all, delete-orphan")
