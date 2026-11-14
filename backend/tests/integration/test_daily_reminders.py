"""FR-6, NFR-4: Integration test for daily reminder execution job.

Verifies:
- Daily reminder job queries reminders due on or before today
- Successfully marks them sent=True
- Does not affect future reminders
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from sqlalchemy.orm import Session

from app.jobs.daily_reminders import run_daily_reminders
from app.models.appliance import Appliance, ApplianceCategory
from app.models.reminder import Reminder
from app.models.user import User


def test_fr6_daily_reminders_job_execution(db_session: Session) -> None:
    """FR-6: Test that daily reminder job marks reminders sent only when due."""
    # 1. Get or create category, user and appliance
    cat = db_session.query(ApplianceCategory).first()
    if not cat:
        cat = ApplianceCategory(
            name="kitchen",
            interval_months=6,
            tips="Regular cleaning",
            guidance_source="general",
        )
        db_session.add(cat)
        db_session.flush()

    user = User(
        name="Reminder Tester",
        email="reminder_runner@example.com",
        password_hash="fakehash",
        consent_given_at=datetime.now(UTC),
    )
    db_session.add(user)
    db_session.flush()

    appliance = Appliance(
        user_id=user.user_id,
        category_id=cat.category_id,
        product_name="Microwave",
        brand="LG",
        model_number="MH2044",
        seller="Croma",
        price=8000.00,
        purchase_date=date(2025, 1, 1),
        warranty_months=12,
        warranty_end_date=date(2026, 1, 1),
    )
    db_session.add(appliance)
    db_session.flush()

    today = date(2026, 3, 15)

    # 2. Add 2 due reminders (one past, one today) and 1 future reminder
    past_due_rem = Reminder(
        user_id=user.user_id,
        appliance_id=appliance.appliance_id,
        type="warranty",
        remind_on=today - timedelta(days=5),
        sent=False,
    )
    today_rem = Reminder(
        user_id=user.user_id,
        appliance_id=appliance.appliance_id,
        type="service",
        remind_on=today,
        sent=False,
    )
    future_rem = Reminder(
        user_id=user.user_id,
        appliance_id=appliance.appliance_id,
        type="warranty",
        remind_on=today + timedelta(days=10),
        sent=False,
    )
    db_session.add_all([past_due_rem, today_rem, future_rem])
    db_session.flush()

    # 3. Execute daily reminder job
    marked_count = run_daily_reminders(db=db_session, today=today)

    assert marked_count == 2
    assert past_due_rem.sent is True
    assert today_rem.sent is True
    assert future_rem.sent is False
