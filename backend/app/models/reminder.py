from datetime import date

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Reminder(Base):
    __tablename__ = "reminders"

    reminder_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    appliance_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("appliances.appliance_id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    service_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("services.service_id", ondelete="CASCADE"), nullable=True, index=True
    )
    liability_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("liabilities.liability_id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    goal_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("goals.goal_id", ondelete="CASCADE"), nullable=True, index=True
    )
    type: Mapped[str] = mapped_column(String(10), nullable=False)  # warranty, service, emi, goal
    remind_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    message: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        CheckConstraint(
            "(CASE WHEN appliance_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN service_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN liability_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN goal_id IS NOT NULL THEN 1 ELSE 0 END) = 1",
            name="chk_reminder_exactly_one_parent",
        ),
    )

    user = relationship("User", back_populates="reminders")
    appliance = relationship("Appliance", back_populates="reminders")
    service = relationship("Service", back_populates="reminders")
    liability = relationship("Liability", back_populates="reminders")
    goal = relationship("Goal", back_populates="reminders")
