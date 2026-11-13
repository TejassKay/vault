"""FR-5, 6.2: Pure service-schedule and reminder-date engine.

All functions are pure: no DB, network, or clock access.
Money uses Decimal; dates are passed in as parameters.
"""

import calendar
from datetime import date, timedelta
from decimal import Decimal
from typing import NamedTuple

# ---------------------------------------------------------------------------
# Warranty helpers
# ---------------------------------------------------------------------------


def warranty_end_date(purchase_date: date, warranty_months: int) -> date:
    """FR-5 / 6.2: Compute warranty end date, clamping to last day of month.

    Example: 2026-01-31 + 1 month → 2026-02-28 (spec example).
    """
    if warranty_months <= 0:
        return purchase_date

    target_year = purchase_date.year + (purchase_date.month - 1 + warranty_months) // 12
    target_month = (purchase_date.month - 1 + warranty_months) % 12 + 1
    # Clamp to last day of target month
    last_day = calendar.monthrange(target_year, target_month)[1]
    target_day = min(purchase_date.day, last_day)
    return date(target_year, target_month, target_day)


# ---------------------------------------------------------------------------
# Service schedule
# ---------------------------------------------------------------------------


class ServiceDate(NamedTuple):
    due_date: date
    guidance_label: str


def build_schedule(
    purchase_date: date,
    warranty_months: int,
    interval_months: int,
    guidance_source: str,
    today: date,
) -> list[ServiceDate]:
    """FR-5 / 6.2: Generate service dates for an appliance.

    Keeps dates where:
      due_date >= today  AND
      due_date <= max(warranty_end_date, today + 12 months)
    """
    if interval_months <= 0:
        return []

    end_date = warranty_end_date(purchase_date, warranty_months)
    cutoff = max(end_date, today + timedelta(days=365))

    result: list[ServiceDate] = []
    k = 1
    while True:
        # service date = purchase_date + k * interval_months calendar months
        svc_date = _add_months(purchase_date, k * interval_months)
        if svc_date > cutoff:
            break
        if svc_date >= today:
            result.append(ServiceDate(due_date=svc_date, guidance_label=guidance_source))
        k += 1

    return result


def _add_months(d: date, months: int) -> date:
    """Add calendar months to a date, clamping to last day of target month."""
    target_year = d.year + (d.month - 1 + months) // 12
    target_month = (d.month - 1 + months) % 12 + 1
    last_day = calendar.monthrange(target_year, target_month)[1]
    target_day = min(d.day, last_day)
    return date(target_year, target_month, target_day)


# ---------------------------------------------------------------------------
# Reminder dates
# ---------------------------------------------------------------------------


class ReminderSpec(NamedTuple):
    remind_on: date
    reminder_type: str  # warranty | service | emi | goal
    message: str


def warranty_reminder_dates(end_date: date, today: date) -> list[ReminderSpec]:
    """6.2: 30 days and 7 days before warranty_end_date, only if in the future."""
    specs: list[ReminderSpec] = []
    for days_before, label in [(30, "30 days"), (7, "7 days")]:
        remind_on = end_date - timedelta(days=days_before)
        if remind_on > today:
            specs.append(
                ReminderSpec(
                    remind_on=remind_on,
                    reminder_type="warranty",
                    message=f"Warranty expires in {label} on {end_date}",
                )
            )
    return specs


def service_reminder_dates(due_date: date, today: date) -> list[ReminderSpec]:
    """6.2: 7 days before service due_date, only if in the future."""
    remind_on = due_date - timedelta(days=7)
    if remind_on > today:
        return [
            ReminderSpec(
                remind_on=remind_on,
                reminder_type="service",
                message=f"Service due on {due_date}",
            )
        ]
    return []


def emi_reminder_date(due_day: int, today: date) -> ReminderSpec | None:
    """6.2: 3 days before next EMI due date, only if in the future."""
    # Determine next due date this or next month
    last_day_this_month = calendar.monthrange(today.year, today.month)[1]
    clamped_day = min(due_day, last_day_this_month)
    candidate = today.replace(day=clamped_day)
    if candidate <= today:
        # Roll to next month
        if today.month == 12:
            next_year, next_month = today.year + 1, 1
        else:
            next_year, next_month = today.year, today.month + 1
        last_day_next = calendar.monthrange(next_year, next_month)[1]
        candidate = date(next_year, next_month, min(due_day, last_day_next))
    remind_on = candidate - timedelta(days=3)
    if remind_on > today:
        return ReminderSpec(
            remind_on=remind_on,
            reminder_type="emi",
            message=f"EMI due on {candidate}",
        )
    return None


def goal_reminder_date(target_date: date, today: date) -> ReminderSpec | None:
    """6.2: 30 days before target_date, only if in the future."""
    remind_on = target_date - timedelta(days=30)
    if remind_on > today:
        return ReminderSpec(
            remind_on=remind_on,
            reminder_type="goal",
            message=f"Goal deadline in 30 days on {target_date}",
        )
    return None


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------
# keep Decimal imported so callers can rely on it from this module
__all__ = [
    "warranty_end_date",
    "build_schedule",
    "ServiceDate",
    "ReminderSpec",
    "warranty_reminder_dates",
    "service_reminder_dates",
    "emi_reminder_date",
    "goal_reminder_date",
    "Decimal",
]
