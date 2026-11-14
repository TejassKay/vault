"""Unit tests for FR-11, FR-12, FR-28: DashboardAggregator pure logic."""

from datetime import date
from decimal import Decimal

from app.engines.dashboard_aggregator import (
    build_dashboard_summary,
    build_timeline_events,
    determine_urgency,
)
from app.engines.financial_engine import FinancialSnapshot


def test_determine_urgency() -> None:
    assert determine_urgency(-1) == "overdue"
    assert determine_urgency(3) == "high"
    assert determine_urgency(20) == "medium"
    assert determine_urgency(45) == "low"


def test_build_timeline_events_and_ordering() -> None:
    today = date(2026, 11, 13)

    liabilities = [
        {
            "liability_id": 1,
            "type": "personal",
            "lender_name": "HDFC",
            "emi_amount": 10000,
            "due_day": 20,
            "status": "active",
        }
    ]
    services = [
        {
            "service_id": 101,
            "product_name": "LG AC",
            "due_date": date(2026, 11, 18),
            "status": "pending",
            "cost": 1500,
            "guidance_label": "general",
        }
    ]
    appliances = [
        {
            "appliance_id": 201,
            "product_name": "Samsung Refrigerator",
            "brand": "Samsung",
            "warranty_end_date": date(2026, 12, 1),
        }
    ]
    goals = [
        {
            "goal_id": 301,
            "title": "Car Down Payment",
            "target_amount": 500000,
            "target_date": date(2028, 11, 13),
            "status": "active",
        }
    ]

    events = build_timeline_events(
        reminders=[],
        liabilities=liabilities,
        services=services,
        appliances=appliances,
        goals=goals,
        today=today,
    )

    assert len(events) == 4
    # Chronological check: Nov 18 (service) < Nov 20 (EMI) < Dec 1 (warranty) < 2028 (goal)
    assert events[0].event_type == "service"
    assert events[0].event_date == date(2026, 11, 18)
    assert events[1].event_type == "emi"
    assert events[1].event_date == date(2026, 11, 20)
    assert events[2].event_type == "warranty"
    assert events[2].event_date == date(2026, 12, 1)
    assert events[3].event_type == "goal"


def test_build_dashboard_summary_aggregation() -> None:
    today = date(2026, 11, 13)
    snap = FinancialSnapshot(
        is_sufficient=True,
        missing_items=[],
        monthly_income=Decimal("85000.00"),
        essential_expenses=Decimal("32000.00"),
        discretionary_expenses=Decimal("8000.00"),
        total_expenses=Decimal("40000.00"),
        debt_payments=Decimal("10000.00"),
        net_cash_flow=Decimal("35000.00"),
        savings_rate=Decimal("41.18"),
        dti=Decimal("11.76"),
        dti_level="low",
        net_worth=Decimal("55000.00"),
        emergency_coverage_months=Decimal("1.07"),
        is_stale=False,
        stale_reasons=[],
    )

    appliances = [
        {
            "appliance_id": 1,
            "product_name": "AC",
            "brand": "Daikin",
            "price": Decimal("45000.00"),
            "warranty_end_date": date(2026, 11, 30),  # 17 days -> asset alert
        }
    ]
    goals = [
        {
            "goal_id": 1,
            "title": "Emergency Fund",
            "target_amount": Decimal("100000.00"),
            "saved_amount": Decimal("25000.00"),
            "target_date": date(2027, 5, 13),
            "status": "active",
        }
    ]

    events = build_timeline_events([], [], [], appliances, goals, today)
    top_rec = {"priority_rank": 1, "rec_type": "EMERGENCY_FUND_LOW", "action": "Build emergency reserve"}

    dash = build_dashboard_summary(
        snapshot=snap,
        investment_capacity=Decimal("0.00"),
        investment_capacity_status="blocked",
        top_recommendation=top_rec,
        timeline_events=events,
        appliances=appliances,
        goals=goals,
        today=today,
    )

    assert dash.snapshot.monthly_income == Decimal("85000.00")
    assert dash.physical_assets_estimate == Decimal("45000.00")
    assert len(dash.asset_alerts) == 1
    assert dash.asset_alerts[0].days_remaining == 17
    assert len(dash.goals_progress) == 1
    assert dash.goals_progress[0].progress_percent == Decimal("25.00")
    assert dash.top_recommendation["rec_type"] == "EMERGENCY_FUND_LOW"
