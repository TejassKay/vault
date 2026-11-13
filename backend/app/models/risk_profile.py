from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RiskProfile(Base):
    __tablename__ = "risk_profiles"

    risk_profile_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    answers: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)  # 8 to 32
    tolerance_level: Mapped[str] = mapped_column(String(12), nullable=False)
    capacity_level: Mapped[str] = mapped_column(String(12), nullable=False)
    effective_level: Mapped[str] = mapped_column(
        String(12), nullable=False
    )  # conservative, moderate, aggressive
    assessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("score >= 8 AND score <= 32", name="chk_risk_score_range"),
        CheckConstraint(
            "effective_level IN ('conservative', 'moderate', 'aggressive')",
            name="chk_risk_effective_level",
        ),
    )

    user = relationship("User", back_populates="risk_profiles")
