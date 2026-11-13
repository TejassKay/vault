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
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ApplianceCategory(Base):
    __tablename__ = "appliance_categories"

    category_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    interval_months: Mapped[int] = mapped_column(Integer, nullable=False)
    tips: Mapped[str | None] = mapped_column(Text, nullable=True)
    guidance_source: Mapped[str] = mapped_column(String(15), nullable=False, default="general")

    __table_args__ = (
        CheckConstraint("interval_months > 0", name="chk_category_interval_positive"),
    )

    appliances = relationship("Appliance", back_populates="category")


class Appliance(Base):
    __tablename__ = "appliances"

    appliance_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("appliance_categories.category_id"), nullable=False, index=True
    )
    bill_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("bills.bill_id", ondelete="SET NULL"), unique=True, nullable=True
    )
    product_name: Mapped[str] = mapped_column(String(100), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    seller: Mapped[str | None] = mapped_column(String(100), nullable=True)
    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)
    warranty_months: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    warranty_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    estimated_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("price IS NULL OR price >= 0", name="chk_appliance_price_non_negative"),
        CheckConstraint("warranty_months >= 0", name="chk_appliance_warranty_months_non_negative"),
    )

    user = relationship("User", back_populates="appliances")
    category = relationship("ApplianceCategory", back_populates="appliances")
    bill = relationship("Bill", back_populates="appliance")
    services = relationship("Service", back_populates="appliance", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="appliance", cascade="all, delete-orphan")


class Service(Base):
    __tablename__ = "services"

    service_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    appliance_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("appliances.appliance_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(10), nullable=False, default="pending"
    )  # pending, done
    completed_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    guidance_label: Mapped[str | None] = mapped_column(
        String(15), nullable=True
    )  # general, manufacturer
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    appliance = relationship("Appliance", back_populates="services")
    reminders = relationship("Reminder", back_populates="service", cascade="all, delete-orphan")
