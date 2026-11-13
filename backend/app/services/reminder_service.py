"""FR-6: Reminder service — creates Reminder rows for appliances, services, liabilities, goals."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.engines.service_scheduler import (
    emi_reminder_date,
    goal_reminder_date,
    service_reminder_dates,
    warranty_reminder_dates,
)
from app.models.appliance import Appliance, Service
from app.models.goal import Goal
from app.models.liability import Liability
from app.models.reminder import Reminder


def create_appliance_reminders(appliance: Appliance, db: Session, today: date) -> list[Reminder]:
    """FR-6: Create warranty reminders (30d + 7d before expiry) for an appliance."""
    specs = warranty_reminder_dates(appliance.warranty_end_date, today)
    reminders: list[Reminder] = []
    for spec in specs:
        reminder = Reminder(
            user_id=appliance.user_id,
            appliance_id=appliance.appliance_id,
            type=spec.reminder_type,
            remind_on=spec.remind_on,
            message=spec.message,
        )
        db.add(reminder)
        reminders.append(reminder)
    return reminders


def create_service_reminders(
    service: Service, appliance: Appliance, db: Session, today: date
) -> list[Reminder]:
    """FR-6: Create service reminder (7d before due_date) for a service record."""
    specs = service_reminder_dates(service.due_date, today)
    reminders: list[Reminder] = []
    for spec in specs:
        reminder = Reminder(
            user_id=appliance.user_id,
            service_id=service.service_id,
            type=spec.reminder_type,
            remind_on=spec.remind_on,
            message=spec.message,
        )
        db.add(reminder)
        reminders.append(reminder)
    return reminders


def create_liability_reminders(liability: Liability, db: Session, today: date) -> list[Reminder]:
    """FR-6: Create EMI reminder (3d before next due date) for a liability."""
    spec = emi_reminder_date(liability.due_day, today)
    if spec:
        reminder = Reminder(
            user_id=liability.user_id,
            liability_id=liability.liability_id,
            type=spec.reminder_type,
            remind_on=spec.remind_on,
            message=spec.message,
        )
        db.add(reminder)
        return [reminder]
    return []


def create_goal_reminders(goal: Goal, db: Session, today: date) -> list[Reminder]:
    """FR-6: Create goal deadline reminder (30d before target_date) for a goal."""
    spec = goal_reminder_date(goal.target_date, today)
    if spec:
        reminder = Reminder(
            user_id=goal.user_id,
            goal_id=goal.goal_id,
            type=spec.reminder_type,
            remind_on=spec.remind_on,
            message=spec.message,
        )
        db.add(reminder)
        return [reminder]
    return []
