"""FR-11, FR-12, FR-28: Pure Aggregator for Dashboard and Timeline.

Pure functions:
- build_dashboard_summary: combines snapshot, obligations, asset alerts, goal progress, top recommendation
- build_timeline_events: extracts and chronologically sorts upcoming obligations (bills, services, warranties, EMIs, goals)

Zero DB, network, or clock access. Pure logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from app.engines.financial_engine import FinancialSnapshot


@dataclass(frozen=True)
class DashboardObligation:
    id: str
    title: str
    due_date: date
    amount: Decimal | None
    category: str  # emi, service, warranty, goal, bill
    status: str  # pending, upcoming, due_soon, overdue
    details: str | None = None


@dataclass(frozen=True)
class DashboardAssetAlert:
    appliance_id: int
    product_name: str
    brand: str | None
    alert_type: str  # warranty_expiring, service_due
    due_date: date
    days_remaining: int
    message: str


@dataclass(frozen=True)
class DashboardGoalSummary:
    goal_id: int
    title: str
    target_amount: Decimal
    saved_amount: Decimal
    progress_percent: Decimal
    target_date: date
    months_left: int
    planning_contribution: Decimal


@dataclass(frozen=True)
class DashboardData:
    snapshot: FinancialSnapshot
    investment_capacity: Decimal | None
    investment_capacity_status: str
    top_recommendation: dict[str, Any] | None
    upcoming_obligations: list[DashboardObligation]
    asset_alerts: list[DashboardAssetAlert]
    goals_progress: list[DashboardGoalSummary]
    physical_assets_estimate: Decimal
    freshness: dict[str, Any]


@dataclass(frozen=True)
class TimelineEvent:
    event_id: str
    title: str
    event_date: date
    event_type: str  # emi, service, warranty, goal, bill
    amount: Decimal | None
    urgency: str  # low, medium, high, overdue
    description: str
    meta: dict[str, Any]


def determine_urgency(days_diff: int) -> str:
    """Classify urgency based on calendar days until due date."""
    if days_diff < 0:
        return "overdue"
    if days_diff <= 7:
        return "high"
    if days_diff <= 30:
        return "medium"
    return "low"


def build_timeline_events(
    reminders: list[dict[str, Any]],
    liabilities: list[dict[str, Any]],
    services: list[dict[str, Any]],
    appliances: list[dict[str, Any]],
    goals: list[dict[str, Any]],
    today: date,
) -> list[TimelineEvent]:
    """FR-12: Produce unified chronologically sorted timeline of events."""
    events: list[TimelineEvent] = []

    # 1. EMIs from active liabilities (next occurrence based on due_day)
    for liab in liabilities:
        if liab.get("status") == "active":
            due_day = liab.get("due_day", 1)
            # Find next due date
            year = today.year
            month = today.month
            try:
                candidate_date = date(year, month, due_day)
            except ValueError:
                # Handle month-end issues (e.g. Feb 30 -> Feb 28)
                import calendar

                last_day = calendar.monthrange(year, month)[1]
                candidate_date = date(year, month, min(due_day, last_day))

            if candidate_date < today:
                # Next month
                if month == 12:
                    month = 1
                    year += 1
                else:
                    month += 1
                import calendar

                last_day = calendar.monthrange(year, month)[1]
                candidate_date = date(year, month, min(due_day, last_day))

            days_diff = (candidate_date - today).days
            events.append(
                TimelineEvent(
                    event_id=f"emi_{liab.get('liability_id')}_{candidate_date.isoformat()}",
                    title=f"EMI: {liab.get('lender_name') or liab.get('type')}",
                    event_date=candidate_date,
                    event_type="emi",
                    amount=Decimal(str(liab.get("emi_amount", "0"))),
                    urgency=determine_urgency(days_diff),
                    description=f"Monthly EMI due for {liab.get('type')} loan",
                    meta={"liability_id": liab.get("liability_id")},
                )
            )

    # 2. Services from scheduled appliances
    for s in services:
        if s.get("status") == "pending":
            due_d = s.get("due_date")
            if isinstance(due_d, str):
                due_d = date.fromisoformat(due_d)
            if due_d >= today:
                days_diff = (due_d - today).days
                app_name = s.get("product_name") or "Appliance"
                events.append(
                    TimelineEvent(
                        event_id=f"service_{s.get('service_id')}",
                        title=f"Service Due: {app_name}",
                        event_date=due_d,
                        event_type="service",
                        amount=Decimal(str(s.get("cost") or 0)) if s.get("cost") else None,
                        urgency=determine_urgency(days_diff),
                        description=s.get("note") or f"Periodic maintenance for {app_name}",
                        meta={
                            "service_id": s.get("service_id"),
                            "guidance": s.get("guidance_label"),
                        },
                    )
                )

    # 3. Warranty expiries
    for a in appliances:
        w_end = a.get("warranty_end_date")
        if isinstance(w_end, str):
            w_end = date.fromisoformat(w_end)
        if w_end and w_end >= today:
            days_diff = (w_end - today).days
            events.append(
                TimelineEvent(
                    event_id=f"warranty_{a.get('appliance_id')}",
                    title=f"Warranty Expiry: {a.get('product_name')}",
                    event_date=w_end,
                    event_type="warranty",
                    amount=None,
                    urgency=determine_urgency(days_diff),
                    description=f"Warranty ends for {a.get('brand', '')} {a.get('product_name')}".strip(),
                    meta={"appliance_id": a.get("appliance_id")},
                )
            )

    # 4. Goal target dates
    for g in goals:
        if g.get("status") == "active":
            t_date = g.get("target_date")
            if isinstance(t_date, str):
                t_date = date.fromisoformat(t_date)
            if t_date and t_date >= today:
                days_diff = (t_date - today).days
                events.append(
                    TimelineEvent(
                        event_id=f"goal_{g.get('goal_id')}",
                        title=f"Goal Deadline: {g.get('title')}",
                        event_date=t_date,
                        event_type="goal",
                        amount=Decimal(str(g.get("target_amount", "0"))),
                        urgency=determine_urgency(days_diff),
                        description=f"Target completion date for {g.get('title')}",
                        meta={"goal_id": g.get("goal_id")},
                    )
                )

    # Sort chronologically
    events.sort(key=lambda x: (x.event_date, 0 if x.urgency == "high" else 1))
    return events


def build_dashboard_summary(
    snapshot: FinancialSnapshot,
    investment_capacity: Decimal | None,
    investment_capacity_status: str,
    top_recommendation: dict[str, Any] | None,
    timeline_events: list[TimelineEvent],
    appliances: list[dict[str, Any]],
    goals: list[dict[str, Any]],
    today: date,
) -> DashboardData:
    """FR-11, FR-18: Aggregate financial snapshot, upcoming obligations, asset alerts, goal progress, and top recommendation."""
    # Upcoming obligations (next 5 chronological events)
    obligations = [
        DashboardObligation(
            id=ev.event_id,
            title=ev.title,
            due_date=ev.event_date,
            amount=ev.amount,
            category=ev.event_type,
            status=ev.urgency,
            details=ev.description,
        )
        for ev in timeline_events[:5]
    ]

    # Asset alerts (warranties expiring in next 60 days, or services due in next 30 days)
    asset_alerts: list[DashboardAssetAlert] = []
    physical_assets_sum = Decimal("0.00")

    for app in appliances:
        # Separate physical asset estimate (FR-18)
        if app.get("price"):
            try:
                physical_assets_sum += Decimal(str(app["price"]))
            except Exception:
                pass
        elif app.get("estimated_value"):
            try:
                physical_assets_sum += Decimal(str(app["estimated_value"]))
            except Exception:
                pass

        w_end = app.get("warranty_end_date")
        if isinstance(w_end, str):
            w_end = date.fromisoformat(w_end)
        if w_end and w_end >= today:
            days = (w_end - today).days
            if days <= 60:
                asset_alerts.append(
                    DashboardAssetAlert(
                        appliance_id=app.get("appliance_id", 0),
                        product_name=app.get("product_name", "Appliance"),
                        brand=app.get("brand"),
                        alert_type="warranty_expiring",
                        due_date=w_end,
                        days_remaining=days,
                        message=f"Warranty expires in {days} days",
                    )
                )

    # Goals progress summary
    goals_progress: list[DashboardGoalSummary] = []
    for g in goals:
        if g.get("status") == "active":
            target = Decimal(str(g.get("target_amount", "0")))
            saved = Decimal(str(g.get("saved_amount", "0")))
            pct = Decimal("0.00")
            if target > Decimal("0"):
                pct = min(Decimal("100.00"), (saved / target) * Decimal("100"))

            t_date = g.get("target_date")
            if isinstance(t_date, str):
                t_date = date.fromisoformat(t_date)

            months_left = max(1, (t_date.year - today.year) * 12 + (t_date.month - today.month))
            planning_contrib = (
                max(Decimal("0"), (target - saved) / Decimal(str(months_left)))
                if target > saved
                else Decimal("0.00")
            )

            goals_progress.append(
                DashboardGoalSummary(
                    goal_id=g.get("goal_id", 0),
                    title=g.get("title", ""),
                    target_amount=target,
                    saved_amount=saved,
                    progress_percent=pct.quantize(Decimal("0.01")),
                    target_date=t_date,
                    months_left=months_left,
                    planning_contribution=planning_contrib.quantize(Decimal("0.01")),
                )
            )

    freshness = {
        "is_stale": snapshot.is_stale,
        "stale_reasons": snapshot.stale_reasons,
        "evaluated_at": today.isoformat(),
    }

    return DashboardData(
        snapshot=snapshot,
        investment_capacity=investment_capacity,
        investment_capacity_status=investment_capacity_status,
        top_recommendation=top_recommendation,
        upcoming_obligations=obligations,
        asset_alerts=asset_alerts,
        goals_progress=goals_progress,
        physical_assets_estimate=physical_assets_sum.quantize(Decimal("0.01")),
        freshness=freshness,
    )
