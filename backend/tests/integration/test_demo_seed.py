"""Spec 6.6: Integration test for demo seed metrics and scenario switching."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.api.routers.dashboard import _extract_user_context
from app.engines.investment_engine import compute_investment_capacity
from app.seed.demo_user import seed_demo_user


def test_spec_6_6_demo_seed_metrics_scenarios_a_and_b(db_session: Session) -> None:
    """Spec 6.6: Net cash flow 35,000, net worth 55,000, emergency coverage 1.07 months; for B, capacity 14,625."""
    today = date(2026, 11, 13)

    # 1. Scenario A
    user_a = seed_demo_user(db_session, scenario="A")
    snap_a, goal_in_a, liab_in_a, hold_in_a, *_ = _extract_user_context(
        db_session, user_a.user_id, today
    )
    assert snap_a.net_cash_flow == Decimal("35000.00")
    assert snap_a.net_worth == Decimal("55000.00")
    assert snap_a.emergency_coverage_months == Decimal("1.07")

    # 2. Scenario B
    user_b = seed_demo_user(db_session, scenario="B")
    snap_b, goal_in_b, liab_in_b, hold_in_b, *_ = _extract_user_context(
        db_session, user_b.user_id, today
    )
    cap_b = compute_investment_capacity(
        snapshot=snap_b,
        goals=goal_in_b,
        liabilities=liab_in_b,
        holdings=hold_in_b,
        today=today,
    )
    assert cap_b.capacity == Decimal("14625.00")
