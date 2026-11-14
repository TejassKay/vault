"""FR-6.6: Golden tests for FinancialEngine and GoalEngine matching spec exact values."""

from datetime import date
from decimal import Decimal

from app.engines.financial_engine import (
    ExpenseInput,
    HoldingInput,
    IncomeInput,
    LiabilityInput,
    compute_financial_snapshot,
)
from app.engines.goal_engine import compute_goal_projection


def test_fr6_6_golden_scenarios_a_and_b() -> None:
    """Part 6.6: Golden test data (demo user, today = 2026-11-13).

    Salary income source: ₹85,000 monthly, fixed.
    Expense transactions in each of Aug, Sep, Oct 2026:
      Rent 18,000, Groceries 8,000, Utilities 3,000, Transport 3,000 (Essential: 32,000)
      Food-out 4,000, Entertainment 4,000 (Discretionary: 8,000)
    Liability: personal loan, outstanding 2,40,000, rate 11.00%, EMI 10,000.
    Goal: Car down payment, target 5,00,000, saved 50,000, target date 2028-11-13.
    """
    today = date(2026, 11, 13)

    # Income
    incomes = [
        IncomeInput(
            amount=Decimal("85000"),
            frequency="monthly",
            is_active=True,
            updated_at=date(2026, 11, 1),
        )
    ]

    # Expenses across 3 months
    expenses: list[ExpenseInput] = []
    for month in [8, 9, 10]:
        expenses.extend(
            [
                ExpenseInput(
                    amount=Decimal("18000"), category="Rent", txn_date=date(2026, month, 5)
                ),
                ExpenseInput(
                    amount=Decimal("8000"), category="Groceries", txn_date=date(2026, month, 10)
                ),
                ExpenseInput(
                    amount=Decimal("3000"), category="Utilities", txn_date=date(2026, month, 15)
                ),
                ExpenseInput(
                    amount=Decimal("3000"), category="Transport", txn_date=date(2026, month, 20)
                ),
                ExpenseInput(
                    amount=Decimal("4000"), category="Food-out", txn_date=date(2026, month, 22)
                ),
                ExpenseInput(
                    amount=Decimal("4000"), category="Entertainment", txn_date=date(2026, month, 25)
                ),
            ]
        )

    liabilities = [
        LiabilityInput(
            outstanding_principal=Decimal("240000"),
            emi_amount=Decimal("10000"),
            interest_rate=Decimal("11.00"),
            status="active",
            updated_at=date(2026, 11, 1),
        )
    ]

    # Scenario A: reserve 45,000
    holdings_a = [
        HoldingInput(
            current_value=Decimal("45000"), is_emergency_reserve=True, as_of_date=date(2026, 11, 1)
        ),
        HoldingInput(
            current_value=Decimal("250000"),
            is_emergency_reserve=False,
            as_of_date=date(2026, 11, 1),
        ),
    ]

    snap_a = compute_financial_snapshot(
        income_sources=incomes,
        income_txns=[],
        expense_txns=expenses,
        liabilities=liabilities,
        holdings=holdings_a,
        today=today,
        expense_months_available=3,
    )

    assert snap_a.is_sufficient is True
    assert snap_a.monthly_income == Decimal("85000.00")
    assert snap_a.essential_expenses == Decimal("32000.00")
    assert snap_a.discretionary_expenses == Decimal("8000.00")
    assert snap_a.debt_payments == Decimal("10000.00")
    assert snap_a.net_cash_flow == Decimal("35000.00")
    assert snap_a.savings_rate == Decimal("41.18")
    assert snap_a.dti == Decimal("11.76")
    assert snap_a.dti_level == "low"
    assert snap_a.net_worth == Decimal("55000.00")
    assert snap_a.emergency_coverage_months == Decimal("1.07")

    # Scenario B: reserve 2,60,000 (total holdings = 2,60,000 + 2,50,000 = 5,10,000)
    holdings_b = [
        HoldingInput(
            current_value=Decimal("260000"), is_emergency_reserve=True, as_of_date=date(2026, 11, 1)
        ),
        HoldingInput(
            current_value=Decimal("250000"),
            is_emergency_reserve=False,
            as_of_date=date(2026, 11, 1),
        ),
    ]

    snap_b = compute_financial_snapshot(
        income_sources=incomes,
        income_txns=[],
        expense_txns=expenses,
        liabilities=liabilities,
        holdings=holdings_b,
        today=today,
        expense_months_available=3,
    )

    assert snap_b.monthly_income == Decimal("85000.00")
    assert snap_b.net_cash_flow == Decimal("35000.00")
    assert snap_b.savings_rate == Decimal("41.18")
    assert snap_b.dti == Decimal("11.76")
    # Net worth: 5,10,000 - 2,40,000 = 2,70,000
    assert snap_b.net_worth == Decimal("270000.00")
    # Emergency coverage: 260,000 / 42,000 = 6.19
    assert snap_b.emergency_coverage_months == Decimal("6.19")


def test_fr6_6_golden_goal_contributions() -> None:
    """Part 6.6: Car down payment goal projections.

    Target 5,00,000, saved 50,000, target_date 2028-11-13 (24 months from 2026-11-13).
    0% scenario -> exactly 18,750
    4% scenario -> ~17,874 (within 1)
    """
    today = date(2026, 11, 13)
    target_date = date(2028, 11, 13)

    proj = compute_goal_projection(
        goal_id=1,
        title="Car down payment",
        target_amount=Decimal("500000"),
        saved_amount=Decimal("50000"),
        target_date=target_date,
        today=today,
    )

    assert proj.months_left == 24
    # 0% scenario
    scenario_0 = next(s for s in proj.scenarios if s.rate_percent == Decimal("0"))
    assert scenario_0.required_monthly_contribution == Decimal("18750.00")
    assert proj.planning_contribution == Decimal("18750.00")

    # 4% scenario
    scenario_4 = next(s for s in proj.scenarios if s.rate_percent == Decimal("4"))
    diff = abs(scenario_4.required_monthly_contribution - Decimal("17874.00"))
    assert diff <= Decimal("2.00")  # within 1-2 rupees of spec approx
