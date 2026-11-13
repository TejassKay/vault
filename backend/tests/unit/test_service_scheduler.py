"""FR-5, 6.2: Unit tests for service_scheduler pure functions — exact values."""

from datetime import date

from app.engines.service_scheduler import (
    build_schedule,
    emi_reminder_date,
    goal_reminder_date,
    service_reminder_dates,
    warranty_end_date,
    warranty_reminder_dates,
)

# ---------------------------------------------------------------------------
# warranty_end_date
# ---------------------------------------------------------------------------


def test_fr5_warranty_end_date_normal() -> None:
    """6.2: Jan 15 + 12 months = Jan 15 next year."""
    result = warranty_end_date(date(2026, 1, 15), 12)
    assert result == date(2027, 1, 15)


def test_fr5_warranty_end_date_month_end_clamp() -> None:
    """6.2: Spec example — 2026-01-31 + 1 month = 2026-02-28 (last day of Feb)."""
    result = warranty_end_date(date(2026, 1, 31), 1)
    assert result == date(2026, 2, 28)


def test_fr5_warranty_end_date_zero_months() -> None:
    """Zero warranty months returns purchase_date unchanged."""
    d = date(2026, 6, 15)
    assert warranty_end_date(d, 0) == d


def test_fr5_warranty_end_date_cross_year() -> None:
    """Nov 30 + 3 months = Feb 28 (next year, Feb clamp)."""
    result = warranty_end_date(date(2026, 11, 30), 3)
    assert result == date(2027, 2, 28)


def test_fr5_warranty_end_date_leap_year() -> None:
    """Jan 31 + 1 month in a leap year = Feb 29."""
    result = warranty_end_date(date(2024, 1, 31), 1)
    assert result == date(2024, 2, 29)


# ---------------------------------------------------------------------------
# build_schedule
# ---------------------------------------------------------------------------


def test_fr5_schedule_dates_ac() -> None:
    """6.2: AC with 6-month interval generates correct service dates."""
    today = date(2026, 1, 1)
    purchase = date(2025, 12, 1)
    # Service dates: 2026-06-01, 2026-12-01, 2027-06-01 ... up to max(warranty_end, today+12mo)
    # warranty 12 months → 2026-12-01; cutoff = max(2026-12-01, 2027-01-01) = 2027-01-01
    result = build_schedule(
        purchase_date=purchase,
        warranty_months=12,
        interval_months=6,
        guidance_source="general",
        today=today,
    )
    due_dates = [s.due_date for s in result]
    assert date(2026, 6, 1) in due_dates
    assert date(2026, 12, 1) in due_dates
    # All dates must be on or after today
    for s in result:
        assert s.due_date >= today


def test_fr5_schedule_guidance_label_propagated() -> None:
    """guidance_source from category is copied to each ServiceDate."""
    result = build_schedule(
        purchase_date=date(2026, 1, 1),
        warranty_months=12,
        interval_months=6,
        guidance_source="manufacturer",
        today=date(2026, 1, 1),
    )
    for s in result:
        assert s.guidance_label == "manufacturer"


def test_fr5_schedule_no_past_dates() -> None:
    """Past service dates are excluded; only future/today dates returned."""
    today = date(2026, 11, 1)
    result = build_schedule(
        purchase_date=date(2024, 1, 1),
        warranty_months=36,
        interval_months=6,
        guidance_source="general",
        today=today,
    )
    for s in result:
        assert s.due_date >= today


def test_fr5_schedule_cutoff_includes_12mo_window() -> None:
    """Even if warranty expired, dates within today+12mo are included."""
    today = date(2026, 11, 1)
    # Short warranty expired in 2025; but interval generates dates into 2027
    result = build_schedule(
        purchase_date=date(2025, 1, 1),
        warranty_months=6,  # expired 2025-07-01
        interval_months=6,
        guidance_source="general",
        today=today,
    )
    # Should include dates up to max(2025-07-01, 2027-11-01) = 2027-11-01
    due_dates = [s.due_date for s in result]
    assert len(due_dates) > 0  # there should be some future dates


# ---------------------------------------------------------------------------
# Reminder dates
# ---------------------------------------------------------------------------


def test_fr6_warranty_reminder_dates_both_future() -> None:
    """6.2: 30d and 7d reminders are both created when in the future."""
    today = date(2026, 11, 1)
    end = date(2027, 6, 1)
    specs = warranty_reminder_dates(end, today)
    remind_ons = [s.remind_on for s in specs]
    assert date(2027, 5, 2) in remind_ons  # 30 days before
    assert date(2027, 5, 25) in remind_ons  # 7 days before


def test_fr6_warranty_reminder_only_future() -> None:
    """6.2: Reminders in the past are excluded."""
    today = date(2027, 5, 10)
    end = date(2027, 6, 1)
    specs = warranty_reminder_dates(end, today)
    # 30d before = 2027-05-02 → past; 7d before = 2027-05-25 → future
    remind_ons = [s.remind_on for s in specs]
    assert date(2027, 5, 2) not in remind_ons
    assert date(2027, 5, 25) in remind_ons


def test_fr6_service_reminder_7d_before() -> None:
    """6.2: Service reminder is 7 days before due_date."""
    today = date(2026, 11, 1)
    due = date(2026, 12, 15)
    specs = service_reminder_dates(due, today)
    assert len(specs) == 1
    assert specs[0].remind_on == date(2026, 12, 8)
    assert specs[0].reminder_type == "service"


def test_fr6_service_reminder_past_excluded() -> None:
    """6.2: Service reminder is not created if 7d before is in the past."""
    today = date(2026, 12, 10)
    due = date(2026, 12, 15)  # 7d before = Dec 8 → past
    specs = service_reminder_dates(due, today)
    assert specs == []


def test_fr6_emi_reminder_3d_before() -> None:
    """6.2: EMI reminder is 3 days before next due date."""
    today = date(2026, 11, 1)
    spec = emi_reminder_date(due_day=10, today=today)
    assert spec is not None
    assert spec.remind_on == date(2026, 11, 7)
    assert spec.reminder_type == "emi"


def test_fr6_goal_reminder_30d_before() -> None:
    """6.2: Goal reminder is 30 days before target_date."""
    today = date(2026, 11, 1)
    target = date(2027, 6, 1)
    spec = goal_reminder_date(target, today)
    assert spec is not None
    assert spec.remind_on == date(2027, 5, 2)
    assert spec.reminder_type == "goal"


def test_fr6_goal_reminder_past_excluded() -> None:
    """6.2: Goal reminder not created if 30d before is in the past."""
    today = date(2027, 5, 10)
    target = date(2027, 6, 1)  # 30d before = 2027-05-02 → past
    spec = goal_reminder_date(target, today)
    assert spec is None
