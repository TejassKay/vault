"""FR-6: Pydantic schemas for Reminder."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict


class ReminderResponse(BaseModel):
    """FR-6: One reminder record."""

    model_config = ConfigDict(from_attributes=True)

    reminder_id: int
    user_id: int
    appliance_id: int | None = None
    service_id: int | None = None
    liability_id: int | None = None
    goal_id: int | None = None
    type: str
    remind_on: date
    message: str | None = None
    sent: bool
