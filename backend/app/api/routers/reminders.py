"""FR-6: Reminders API and daily reminder job trigger."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.jobs.daily_reminders import run_daily_reminders
from app.models.reminder import Reminder
from app.models.user import User
from app.schemas.reminder import ReminderResponse

router = APIRouter(tags=["reminders"])


@router.get("/reminders", response_model=list[ReminderResponse])
def list_reminders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ReminderResponse]:
    """FR-6, NFR-3: Get user's upcoming reminders (not sent, remind_on >= today)."""
    today = date.today()
    reminders = (
        db.query(Reminder)
        .filter(
            Reminder.user_id == current_user.user_id,
            Reminder.sent == False,  # noqa: E712
            Reminder.remind_on >= today,
        )
        .order_by(Reminder.remind_on.asc())
        .all()
    )
    return [ReminderResponse.model_validate(r) for r in reminders]


@router.post("/jobs/daily-reminders", status_code=status.HTTP_200_OK)
def trigger_daily_reminders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # noqa: ARG001
) -> dict[str, int]:
    """FR-6, NFR-4: Dev/admin endpoint to trigger the daily reminder job manually."""
    today = date.today()
    count = run_daily_reminders(db, today)
    return {"reminders_sent": count}
