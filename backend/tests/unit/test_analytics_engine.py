"""Unit tests for pure analytics engine (engines/analytics.py)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.engines.analytics import (
    AnalyticsHoldingInput,
    AnalyticsLiabilityInput,
    compute_analytics_summary,
)
from app.engines.financial_engine import ExpenseInput, IncomeInput


def test_analytics_engine_empty_user() -> None:
    summary = compute_analytics_summary(
        income_sources=[],
        income_txns=[],
        expense_txns=[],
        liabilities=[],
        holdings=[],
        selected_month_start=date(2026, 11, 1),
        months=6,
        today=date(2026, 11, 14),
    )
    assert summary.has_data is False
    assert summary.months_available == 0
    assert summary.category_breakdown.items == []
    assert summary.category_breakdown.total == Decimal("0.00")
    assert len(summary.monthly_series) == 7
    assert all(m.expenses == Decimal("0.00") for m in summary.monthly_series)
    assert summary.compare == []
    assert summary.composition.holdings_total == Decimal("0.00")
    assert summary.composition.liabilities_total == Decimal("0.00")


def test_analytics_engine_calculations_emi_exclusion_and_top5() -> None:
    today = date(2026, 11, 14)
    income_sources = [
        IncomeInput(
            amount=Decimal("100000"),
            frequency="monthly",
            is_active=True,
            updated_at=date(2026, 11, 1),
        )
    ]
    expense_txns = [
        # October 2026 (previous month)
        ExpenseInput(amount=Decimal("20000"), category="Rent", txn_date=date(2026, 10, 2)),
        ExpenseInput(amount=Decimal("8000"), category="Groceries", txn_date=date(2026, 10, 5)),
        ExpenseInput(amount=Decimal("5000"), category="EMI", txn_date=date(2026, 10, 5)),
        ExpenseInput(amount=Decimal("3000"), category="Dining", txn_date=date(2026, 10, 10)),
        # November 2026 (selected month) - 7 non-EMI categories to trigger "Other"
        ExpenseInput(amount=Decimal("20000"), category="Rent", txn_date=date(2026, 11, 2)),
        ExpenseInput(amount=Decimal("9000"), category="Groceries", txn_date=date(2026, 11, 4)),
        ExpenseInput(amount=Decimal("7000"), category="Shopping", txn_date=date(2026, 11, 6)),
        ExpenseInput(amount=Decimal("4000"), category="Utilities", txn_date=date(2026, 11, 7)),
        ExpenseInput(amount=Decimal("3000"), category="Transport", txn_date=date(2026, 11, 8)),
        ExpenseInput(amount=Decimal("2000"), category="Dining", txn_date=date(2026, 11, 9)),
        ExpenseInput(amount=Decimal("1000"), category="Health", txn_date=date(2026, 11, 10)),
        ExpenseInput(amount=Decimal("5000"), category="EMI", txn_date=date(2026, 11, 5)),
    ]
    liabilities = [
        AnalyticsLiabilityInput(
            type="personal",
            outstanding_principal=Decimal("150000"),
            emi_amount=Decimal("5000"),
            status="active",
        ),
        AnalyticsLiabilityInput(
            type="vehicle",
            outstanding_principal=Decimal("50000"),
            emi_amount=Decimal("3000"),
            status="closed",
        ),
    ]
    holdings = [
        AnalyticsHoldingInput(type="bank_savings", current_value=Decimal("100000")),
        AnalyticsHoldingInput(type="mutual_fund", current_value=Decimal("300000")),
    ]

    summary = compute_analytics_summary(
        income_sources=income_sources,
        income_txns=[],
        expense_txns=expense_txns,
        liabilities=liabilities,
        holdings=holdings,
        selected_month_start=date(2026, 11, 1),
        months=3,
        today=today,
    )

    assert summary.has_data is True
    assert summary.months_available == 2
    # EMI excluded: 20000+9000+7000+4000+3000+2000+1000 = 46000
    assert summary.category_breakdown.total == Decimal("46000.00")
    assert summary.category_breakdown.items[0].category == "Rent"
    assert summary.category_breakdown.items[0].share_percent == Decimal("43.48")
    assert all(item.category.lower() != "emi" for item in summary.category_breakdown.items)

    # Monthly series: 3 prior + selected = 4 months
    assert len(summary.monthly_series) == 4
    nov = summary.monthly_series[-1]
    assert nov.month == "2026-11"
    assert nov.income == Decimal("100000.00")
    # Essential: Rent 20k + Groceries 9k + Utilities 4k + Transport 3k + Health 1k = 37k
    assert nov.essential == Decimal("37000.00")
    # Discretionary: Shopping 7k + Dining 2k = 9k
    assert nov.discretionary == Decimal("9000.00")
    assert nov.expenses == Decimal("46000.00")
    assert nov.net == Decimal("54000.00")
    assert nov.debt_payments == Decimal("5000.00")

    # Category trend: top 5 + Other
    assert len(summary.category_trend.categories) == 6
    assert summary.category_trend.categories[-1] == "Other"
    nov_trend = summary.category_trend.series[-1]
    assert nov_trend.totals["Other"] > Decimal("0")

    # Spending pace
    assert summary.spending_pace.comparison_day == 14
    assert len(summary.spending_pace.current_month) == 14
    assert len(summary.spending_pace.previous_month) == 31
    assert summary.spending_pace.delta_at_day == Decimal("15000.00")

    # Compare: Shopping has previous=0 -> delta_percent is None
    shopping_cmp = next(c for c in summary.compare if c.category == "Shopping")
    assert shopping_cmp.delta == Decimal("7000.00")
    assert shopping_cmp.delta_percent is None

    # Composition: closed liability excluded
    assert summary.composition.holdings_total == Decimal("400000.00")
    assert summary.composition.liabilities_total == Decimal("150000.00")
    assert len(summary.composition.liabilities_items) == 1
