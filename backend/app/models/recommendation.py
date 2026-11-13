from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    recommendation_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    priority_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    rec_type: Mapped[str] = mapped_column(String(30), nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    assumptions: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONB, nullable=True)
    risks: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONB, nullable=True)
    alternatives: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONB, nullable=True)
    review_trigger: Mapped[str | None] = mapped_column(String(255), nullable=True)
    inputs_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    engine_version: Mapped[str] = mapped_column(String(10), nullable=False)
    explanation_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation_source: Mapped[str | None] = mapped_column(
        String(10), nullable=True
    )  # llm, template
    status: Mapped[str] = mapped_column(
        String(10), nullable=False, default="proposed"
    )  # proposed, accepted, edited, rejected
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('proposed', 'accepted', 'edited', 'rejected')",
            name="chk_recommendation_status",
        ),
        CheckConstraint(
            "explanation_source IS NULL OR explanation_source IN ('llm', 'template')",
            name="chk_recommendation_explanation_source",
        ),
    )

    user = relationship("User", back_populates="recommendations")
