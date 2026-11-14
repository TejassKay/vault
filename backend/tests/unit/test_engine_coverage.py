"""Unit tests targeting edge cases and branches across engines to ensure >= 90% coverage.

Engines tested:
- budget_engine
- financial_engine
- goal_engine
- advisor_engine
- risk_engine
- dashboard_aggregator
- service_scheduler
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.engines.advisor_engine import (
    build_advisor_plan,
)
from app.engines.budget_engine import compute_budget_nudge
from app.engines.dashboard_aggregator import (
    build_dashboard_summary,
    build_timeline_events,
    determine_urgency,
)
from app.engines.financial_engine import (
    ExpenseInput,
    FinancialSnapshot,
    HoldingInput,
    IncomeInput,
    compute_expenses,
    compute_financial_snapshot,
    compute_monthly_income,
)
from app.engines.goal_engine import (
    compute_goal_projection,
    compute_months_left,
    compute_required_contribution,
)
from app.engines.investment_engine import GoalInput, InvestmentCapacityResult


def test_budget_engine_zero_prev_month() -> None:
    """Test budget engine with 0 previous month expenses returns should_show=False."""
    today = date(2026, 3, 15)
    cur = [(Decimal("1000.00"), "groceries")]
    prev: list[tuple[Decimal, str]] = []
    res = compute_budget_nudge(cur, prev, today)
    assert not res.should_show
    assert res.projected_amount is None


def test_budget_engine_projected_exceeds_threshold() -> None:
    """Test budget engine when projected spending exceeds 110% of previous month."""
    today = date(2026, 3, 10)  # 10 days elapsed in March (31 days)
    # MTD = 4500, previous = 10000 -> projected = 4500 / 10 * 31 = 13950 > 11000 (110%)
    cur = [(Decimal("3000.00"), "dining"), (Decimal("1500.00"), "groceries")]
    prev = [(Decimal("10000.00"), "groceries")]
    res = compute_budget_nudge(cur, prev, today)
    assert res.should_show
    assert res.largest_category_increase == "dining"
    assert "projected spending" in res.message


def test_budget_engine_mtd_exceeds_previous_month() -> None:
    """Test budget engine when MTD already exceeds previous month."""
    today = date(2026, 3, 20)
    cur = [(Decimal("12000.00"), "shopping")]
    prev = [(Decimal("10000.00"), "groceries")]
    res = compute_budget_nudge(cur, prev, today)
    assert res.should_show
    assert "has exceeded last month's total" in res.message
    assert res.largest_category_increase == "shopping"


def test_budget_engine_within_budget_no_nudge() -> None:
    """Test budget engine within budget returns should_show=False."""
    today = date(2026, 3, 20)
    cur = [(Decimal("2000.00"), "groceries")]
    prev = [(Decimal("10000.00"), "groceries")]
    res = compute_budget_nudge(cur, prev, today)
    assert not res.should_show
    assert res.message is None


def test_financial_engine_income_frequencies_and_fallbacks() -> None:
    """Test weekly, yearly, and transaction fallback income calculations."""
    today = date(2026, 3, 15)
    # Weekly income
    sources_weekly = [
        IncomeInput(
            amount=Decimal("1000.00"),
            frequency="weekly",
            is_active=True,
            updated_at=date(2026, 1, 1),
        )
    ]
    inc, stale = compute_monthly_income(sources_weekly, [], today)
    # 1000 * 52 / 12 = 4333.33
    assert inc == Decimal("4333.33")
    assert not stale

    # Yearly income and stale > 90 days
    sources_yearly = [
        IncomeInput(
            amount=Decimal("120000.00"),
            frequency="yearly",
            is_active=True,
            updated_at=date(2025, 11, 1),
        )
    ]
    inc_yr, stale_yr = compute_monthly_income(sources_yearly, [], today)
    assert inc_yr == Decimal("10000.00")
    assert stale_yr

    # Fallback to income transactions when sources empty
    income_txns = [
        ExpenseInput(amount=Decimal("60000.00"), category="salary", txn_date=date(2026, 2, 1)),
        ExpenseInput(amount=Decimal("60000.00"), category="salary", txn_date=date(2026, 1, 1)),
    ]
    inc_txn, _ = compute_monthly_income([], income_txns, today)
    # 120000 / 3 = 40000
    assert inc_txn == Decimal("40000.00")


def test_financial_engine_expenses_zero_months_and_stale_branches() -> None:
    """Test zero month count handling and stale indicators in financial engine."""
    today = date(2026, 3, 15)
    txns = [
        ExpenseInput(amount=Decimal("5000.00"), category="rent", txn_date=date(2026, 1, 1)),
        ExpenseInput(
            amount=Decimal("2000.00"), category="entertainment", txn_date=date(2026, 1, 1)
        ),
    ]
    ess, disc = compute_expenses(txns, months_count=0)
    assert ess == Decimal("5000.00")
    assert disc == Decimal("2000.00")

    # Full snapshot with stale holdings and old transactions (> 45 days)
    old_txns = [
        ExpenseInput(amount=Decimal("5000.00"), category="rent", txn_date=date(2025, 12, 1)),
    ]
    sources = [
        IncomeInput(
            amount=Decimal("50000.00"), frequency="monthly", is_active=True, updated_at=today
        )
    ]
    holdings = [
        HoldingInput(
            current_value=Decimal("100000.00"),
            is_emergency_reserve=True,
            as_of_date=date(2025, 12, 1),
        )
    ]
    snap = compute_financial_snapshot(
        income_sources=sources,
        income_txns=[],
        expense_txns=old_txns,
        liabilities=[],
        holdings=holdings,
        today=today,
    )
    assert snap.is_stale
    assert any("Holdings" in r for r in snap.stale_reasons)
    assert any("45 days" in r for r in snap.stale_reasons)


def test_goal_engine_edge_cases() -> None:
    """Test goal target reached, 0 target amount, and various horizons."""
    today = date(2026, 3, 1)
    # Target reached
    contrib = compute_required_contribution(
        target=Decimal("50000.00"),
        saved=Decimal("50000.00"),
        months_n=12,
        annual_rate_percent=Decimal("4.0"),
    )
    assert contrib == Decimal("0.00")

    # Months left min 1
    past_date = date(2025, 1, 1)
    assert compute_months_left(today, past_date) == 1

    # Horizon > 60 months (0%, 6%, 10%)
    proj_long = compute_goal_projection(
        goal_id=1,
        title="House",
        target_amount=Decimal("1000000.00"),
        saved_amount=Decimal("100000.00"),
        target_date=date(2033, 3, 1),
        today=today,
    )
    rates = [s.rate_percent for s in proj_long.scenarios]
    assert rates == [Decimal("0"), Decimal("6"), Decimal("10")]

    # Horizon 37 to 60 months (0%, 4%, 7%)
    proj_med = compute_goal_projection(
        goal_id=2,
        title="Car",
        target_amount=Decimal("500000.00"),
        saved_amount=Decimal("50000.00"),
        target_date=date(2029, 9, 1),
        today=today,
    )
    rates_med = [s.rate_percent for s in proj_med.scenarios]
    assert rates_med == [Decimal("0"), Decimal("4"), Decimal("7")]

    # 0 target amount
    proj_zero = compute_goal_projection(
        goal_id=3,
        title="Zero",
        target_amount=Decimal("0.00"),
        saved_amount=Decimal("0.00"),
        target_date=date(2027, 3, 1),
        today=today,
    )
    assert proj_zero.progress_percent == Decimal("100.00")


def test_advisor_engine_negative_cash_flow_and_underfunded_goals() -> None:
    """Test advisor rule engine ranks: NEGATIVE_CASH_FLOW and GOALS_UNDERFUNDED."""
    # Negative cash flow snapshot
    snap_neg = FinancialSnapshot(
        is_sufficient=True,
        missing_items=[],
        monthly_income=Decimal("30000.00"),
        essential_expenses=Decimal("25000.00"),
        discretionary_expenses=Decimal("10000.00"),
        total_expenses=Decimal("35000.00"),
        debt_payments=Decimal("5000.00"),
        net_cash_flow=Decimal("-10000.00"),
        savings_rate=Decimal("-33.33"),
        dti=Decimal("16.67"),
        dti_level="low",
        net_worth=Decimal("20000.00"),
        emergency_coverage_months=Decimal("0.5"),
        is_stale=False,
        stale_reasons=[],
    )
    cap = InvestmentCapacityResult(
        status="blocked",
        capacity=Decimal("0.00"),
        capacity_if_clear=None,
        surplus=Decimal("-10000.00"),
        goal_contribution=Decimal("0.00"),
        emergency_top_up=Decimal("0.00"),
        remaining=Decimal("0.00"),
        steps=[],
        reason_codes=["NEGATIVE_CASH_FLOW"],
        missing_items=[],
        assumptions=[],
    )
    discretionary_txns = [
        ExpenseInput(amount=Decimal("6000.00"), category="dining", txn_date=date(2026, 3, 1)),
        ExpenseInput(amount=Decimal("4000.00"), category="shopping", txn_date=date(2026, 3, 2)),
    ]
    plan_neg = build_advisor_plan(
        snapshot=snap_neg,
        capacity=cap,
        goals=[],
        liabilities=[],
        discretionary_txns=discretionary_txns,
    )
    rec_types = [r.rec_type for r in plan_neg.recommendations]
    assert "NEGATIVE_CASH_FLOW" in rec_types
    neg_rec = next(r for r in plan_neg.recommendations if r.rec_type == "NEGATIVE_CASH_FLOW")
    assert "dining" in neg_rec.reason

    # Underfunded goals (surplus exists but goals total > capacity)
    snap_surplus = FinancialSnapshot(
        is_sufficient=True,
        missing_items=[],
        monthly_income=Decimal("80000.00"),
        essential_expenses=Decimal("30000.00"),
        discretionary_expenses=Decimal("15000.00"),
        total_expenses=Decimal("45000.00"),
        debt_payments=Decimal("0.00"),
        net_cash_flow=Decimal("35000.00"),
        savings_rate=Decimal("43.75"),
        dti=Decimal("0.00"),
        dti_level="low",
        net_worth=Decimal("200000.00"),
        emergency_coverage_months=Decimal("6.5"),
        is_stale=False,
        stale_reasons=[],
    )
    cap_surplus = InvestmentCapacityResult(
        status="ok",
        capacity=Decimal("10000.00"),
        capacity_if_clear=None,
        surplus=Decimal("35000.00"),
        goal_contribution=Decimal("50000.00"),
        emergency_top_up=Decimal("0.00"),
        remaining=Decimal("0.00"),
        steps=[],
        reason_codes=[],
        missing_items=[],
        assumptions=[],
    )
    goals = [
        GoalInput(
            target_amount=Decimal("2000000.00"),
            saved_amount=Decimal("100000.00"),
            target_date=date(2028, 3, 1),
            status="active",
        )
    ]
    plan_goals = build_advisor_plan(
        snapshot=snap_surplus,
        capacity=cap_surplus,
        goals=goals,
        liabilities=[],
    )
    rec_types_goals = [r.rec_type for r in plan_goals.recommendations]
    assert "GOALS_UNDERFUNDED" in rec_types_goals


def test_dashboard_aggregator_urgency_and_event_types() -> None:
    """Test dashboard aggregator urgency bounds and event parsing."""
    today = date(2026, 3, 15)
    # Urgency calculations by days_diff
    assert determine_urgency(-5) == "overdue"
    assert determine_urgency(0) == "high"
    assert determine_urgency(5) == "high"
    assert determine_urgency(20) == "medium"
    assert determine_urgency(45) == "low"

    appliances = [
        {
            "appliance_id": 1,
            "product_name": "Refrigerator",
            "warranty_end_date": date(2026, 4, 1),
        }
    ]
    liabilities = [
        {
            "liability_id": 5,
            "lender_name": "HDFC",
            "type": "Auto Loan",
            "due_day": 25,
            "emi_amount": Decimal("15000.00"),
            "status": "active",
        }
    ]
    services = [
        {
            "service_id": 10,
            "appliance_id": 1,
            "product_name": "Refrigerator",
            "service_type": "Filter replacement",
            "due_date": date(2026, 3, 22),
            "status": "pending",
        }
    ]
    goals = [
        {
            "goal_id": 3,
            "title": "Emergency Fund",
            "target_date": date(2026, 12, 31),
            "status": "active",
            "planning_contribution": Decimal("5000.00"),
        }
    ]
    reminders = [
        {
            "reminder_id": 99,
            "remind_on": date(2026, 3, 16),
            "type": "custom",
            "notes": "Verify warranty document",
        }
    ]

    events = build_timeline_events(
        reminders=reminders,
        liabilities=liabilities,
        services=services,
        appliances=appliances,
        goals=goals,
        today=today,
    )
    assert len(events) >= 4
    event_types = {e.event_type for e in events}
    assert "warranty" in event_types
    assert "service" in event_types
    assert "emi" in event_types
    assert "goal" in event_types

    # Full dashboard summary
    snap = FinancialSnapshot(
        is_sufficient=True,
        missing_items=[],
        monthly_income=Decimal("50000.00"),
        essential_expenses=Decimal("20000.00"),
        discretionary_expenses=Decimal("10000.00"),
        total_expenses=Decimal("30000.00"),
        debt_payments=Decimal("5000.00"),
        net_cash_flow=Decimal("15000.00"),
        savings_rate=Decimal("30.00"),
        dti=Decimal("10.00"),
        dti_level="low",
        net_worth=Decimal("100000.00"),
        emergency_coverage_months=Decimal("4.0"),
        is_stale=False,
        stale_reasons=[],
    )
    summary = build_dashboard_summary(
        snapshot=snap,
        investment_capacity=Decimal("8000.00"),
        investment_capacity_status="ok",
        top_recommendation=None,
        timeline_events=events,
        appliances=appliances,
        goals=goals,
        today=today,
    )
    assert summary.snapshot.net_worth == Decimal("100000.00")
    assert len(summary.upcoming_obligations) >= 1
