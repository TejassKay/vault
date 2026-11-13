from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Bill(Base):
    __tablename__ = "bills"

    bill_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(5), nullable=False)  # pdf, jpg, png
    parse_status: Mapped[str] = mapped_column(
        String(15), nullable=False, default="pending"
    )  # pending, parsed, needs_review, corrected
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extraction_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    corrected_fields: Mapped[list[str] | dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="bills")
    appliance = relationship("Appliance", back_populates="bill", uselist=False)
