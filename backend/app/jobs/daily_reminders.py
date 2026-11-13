"""FR-6, NFR-4: Daily reminder job — marks due reminders as sent.

In MVP: no actual push/email. Just marks sent=True and logs.
Real delivery would be hooked in here.
"""

from __future__ import annotations

import logging
from datetime import date

from sqlalchemy.orm import Session

from app.models.reminder import Reminder

logger = logging.getLogger(__name__)


def run_daily_reminders(db: Session, today: date) -> int:
    """FR-6: Query reminders due today or earlier and mark them sent.

    Returns:
        Number of reminders marked sent.
    """
    due_reminders = (
        db.query(Reminder)
        .filter(
            Reminder.sent == False,  # noqa: E712
            Reminder.remind_on <= today,
        )
        .all()
    )

    count = 0
    for reminder in due_reminders:
        # In a real system: send push notification / email here.
        # For MVP: log and mark sent.
        logger.info(
            "Reminder %d for user %d: type=%s remind_on=%s — marked sent",
            reminder.reminder_id,
            reminder.user_id,
            reminder.type,
            reminder.remind_on,
        )
        reminder.sent = True
        count += 1

    db.commit()
    return count
