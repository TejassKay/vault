"""Targeted coverage booster to bring advisor_engine, financial_engine, and dashboard_aggregator all >= 90%."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.engines.advisor_engine import (
    build_advisor_plan,
)
from app.engines.dashboard_aggregator import (
    build_dashboard_summary,
    build_timeline_events,
)
from app.engines.financial_engine import (
    ExpenseInput,
    FinancialSnapshot,
    IncomeInput,
    LiabilityInput,
    compute_financial_snapshot,
)
from app.engines.investment_engine import InvestmentCapacityResult


def test_advisor_engine_emergency_build_and_high_interest() -> None:
    """Test Rank 4 EMERGENCY_FUND_BUILD and Rank 2 HIGH_INTEREST_DEBT in advisor_engine."""
    today = date(2026, 3, 15)
    snap = FinancialSnapshot(
        is_sufficient=True,
        missing_items=[],
        monthly_income=Decimal("60000.00"),
        essential_expenses=Decimal("20000.00"),
        discretionary_expenses=Decimal("10000.00"),
        total_expenses=Decimal("30000.00"),
        debt_payments=Decimal("5000.00"),
        net_cash_flow=Decimal("25000.00"),
        savings_rate=Decimal("41.67"),
        dti=Decimal("8.33"),
        dti_level="low",
        net_worth=Decimal("150000.00"),
        emergency_coverage_months=Decimal("4.50"),  # Between 3 and 6
        is_stale=False,
        stale_reasons=[],
    )
    cap = InvestmentCapacityResult(
        status="ok",
        capacity=Decimal("15000.00"),
        capacity_if_clear=None,
        surplus=Decimal("25000.00"),
        goal_contribution=Decimal("0.00"),
        emergency_top_up=Decimal("3125.00"),
        remaining=Decimal("15000.00"),
        steps=[],
        reason_codes=[],
        missing_items=[],
        assumptions=[],
    )
    liabs = [
        LiabilityInput(
            outstanding_principal=Decimal("50000.00"),
            emi_amount=Decimal("5000.00"),
            interest_rate=Decimal("14.50"),  # > 12% triggers high interest
            status="active",
            updated_at=today,
        )
    ]
    plan = build_advisor_plan(
        snapshot=snap,
        capacity=cap,
        goals=[],
        liabilities=liabs,
    )
    rec_types = [r.rec_type for r in plan.recommendations]
    assert "HIGH_INTEREST_DEBT" in rec_types
    assert "EMERGENCY_FUND_BUILD" in rec_types


def test_financial_engine_dti_levels_and_stale_liabilities() -> None:
    """Test DTI moderate/high and stale liability triggers in financial_engine."""
    today = date(2026, 3, 15)
    # DTI moderate (e.g. 30%) and DTI high (e.g. 50%)
    sources = [
        IncomeInput(
            amount=Decimal("10000.00"),
            frequency="monthly",
            is_active=True,
            updated_at=today,
        )
    ]
    txns = [
        ExpenseInput(
            amount=Decimal("2000.00"),
            category="groceries",
            txn_date=today,
        )
    ]
    stale_liabs = [
        LiabilityInput(
            outstanding_principal=Decimal("100000.00"),
            emi_amount=Decimal("5000.00"),  # 50% DTI -> high
            interest_rate=Decimal("10.00"),
            status="active",
            updated_at=date(2026, 1, 1),  # > 30 days -> stale
        )
    ]
    snap = compute_financial_snapshot(
        income_sources=sources,
        income_txns=[],
        expense_txns=txns,
        liabilities=stale_liabs,
        holdings=[],
        today=today,
    )
    assert snap.dti_level == "high"
    assert snap.is_stale
    assert any("Liabilities" in r for r in snap.stale_reasons)


def test_dashboard_aggregator_pending_services_and_reminders() -> None:
    """Test pending services and physical asset calculation in dashboard_aggregator."""
    today = date(2026, 3, 15)
    services = [
        {
            "service_id": 1,
            "product_name": "AC",
            "due_date": "2026-03-25",
            "status": "pending",
            "cost": 1500.0,
            "note": "Deep clean",
            "guidance_label": "Recommended",
        }
    ]
    appliances = [
        {
            "appliance_id": 10,
            "product_name": "Laptop",
            "price": 85000.0,
            "warranty_end_date": "2026-04-10",
        }
    ]
    events = build_timeline_events(
        reminders=[],
        liabilities=[],
        services=services,
        appliances=appliances,
        goals=[],
        today=today,
    )
    assert any(e.event_type == "service" for e in events)
    assert any(e.event_type == "warranty" for e in events)

    snap = FinancialSnapshot(
        is_sufficient=True,
        missing_items=[],
        monthly_income=Decimal("50000.00"),
        essential_expenses=Decimal("20000.00"),
        discretionary_expenses=Decimal("10000.00"),
        total_expenses=Decimal("30000.00"),
        debt_payments=Decimal("0.00"),
        net_cash_flow=Decimal("20000.00"),
        savings_rate=Decimal("40.00"),
        dti=Decimal("0.00"),
        dti_level="low",
        net_worth=Decimal("200000.00"),
        emergency_coverage_months=Decimal("8.0"),
        is_stale=False,
        stale_reasons=[],
    )
    summary = build_dashboard_summary(
        snapshot=snap,
        investment_capacity=Decimal("15000.00"),
        investment_capacity_status="ok",
        top_recommendation=None,
        timeline_events=events,
        appliances=appliances,
        goals=[],
        today=today,
    )
    assert summary.physical_assets_estimate == Decimal("85000.00")
    assert len(summary.asset_alerts) >= 1
