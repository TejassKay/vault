"""FR-10, FR-18, FR-19, FR-20, 6.4: Pure Financial Engine.

Calculates:
- Monthly income
- Expenses (Essential vs Discretionary)
- Debt payments
- Net cash flow
- Savings rate
- Debt-to-Income (DTI)
- Net worth
- Emergency fund coverage (months)
- Freshness indicators

Zero DB, network, or clock access. Pure Decimal arithmetic.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

ESSENTIAL_CATEGORIES = {
    "rent",
    "groceries",
    "utilities",
    "transport",
    "health",
    "education",
    "insurance",
}


def round_cur(val: Decimal) -> Decimal:
    """Round to 2 decimal places half-up."""
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class IncomeInput:
    amount: Decimal
    frequency: str  # monthly, weekly, yearly, one_time
    is_active: bool
    updated_at: date


@dataclass(frozen=True)
class ExpenseInput:
    amount: Decimal
    category: str
    txn_date: date


@dataclass(frozen=True)
class LiabilityInput:
    outstanding_principal: Decimal
    emi_amount: Decimal
    interest_rate: Decimal
    status: str  # active, closed
    updated_at: date


@dataclass(frozen=True)
class HoldingInput:
    current_value: Decimal
    is_emergency_reserve: bool
    as_of_date: date


@dataclass(frozen=True)
class FinancialSnapshot:
    is_sufficient: bool
    missing_items: list[str]
    monthly_income: Decimal
    essential_expenses: Decimal
    discretionary_expenses: Decimal
    total_expenses: Decimal
    debt_payments: Decimal
    net_cash_flow: Decimal
    savings_rate: Decimal  # percentage
    dti: Decimal  # percentage
    dti_level: str  # low, moderate, high
    net_worth: Decimal
    emergency_coverage_months: Decimal
    is_stale: bool
    stale_reasons: list[str]


def compute_monthly_income(
    income_sources: list[IncomeInput],
    income_txns: list[ExpenseInput],
    today: date,
) -> tuple[Decimal | None, bool]:
    """Calculate normalized monthly income."""
    active_sources = [s for s in income_sources if s.is_active and s.frequency != "one_time"]
    if active_sources:
        total = Decimal("0")
        is_stale = False
        for s in active_sources:
            if (today - s.updated_at).days > 90:
                is_stale = True
            if s.frequency == "monthly":
                total += s.amount
            elif s.frequency == "weekly":
                total += (s.amount * Decimal("52")) / Decimal("12")
            elif s.frequency == "yearly":
                total += s.amount / Decimal("12")
        return round_cur(total), is_stale

    # Fallback to last 3 months average income txns
    if income_txns:
        # Sum over available transactions / 3 (or distinct months)
        total_txns = sum(t.amount for t in income_txns)
        return round_cur(total_txns / Decimal("3")), False

    return None, False


def compute_expenses(
    expense_txns: list[ExpenseInput],
    months_count: int = 3,
) -> tuple[Decimal, Decimal]:
    """Calculate average essential and discretionary expenses excluding EMI.

    Returns: (essential, discretionary)
    """
    if months_count <= 0:
        months_count = 1

    essential_sum = Decimal("0")
    discretionary_sum = Decimal("0")

    for t in expense_txns:
        cat = t.category.strip().lower()
        if cat == "emi":
            continue  # Exclude EMI since it comes from liabilities
        if cat in ESSENTIAL_CATEGORIES:
            essential_sum += t.amount
        else:
            discretionary_sum += t.amount

    m_div = Decimal(str(months_count))
    return round_cur(essential_sum / m_div), round_cur(discretionary_sum / m_div)


def _month_start_offset(month_start: date, offset: int) -> date:
    """Return the 1st of the calendar month shifted by `offset` months."""
    total_months = month_start.year * 12 + (month_start.month - 1) + offset
    year, month_idx = divmod(total_months, 12)
    return date(year, month_idx + 1, 1)


def compute_financial_snapshot(
    income_sources: list[IncomeInput],
    income_txns: list[ExpenseInput],
    expense_txns: list[ExpenseInput],
    liabilities: list[LiabilityInput],
    holdings: list[HoldingInput],
    today: date,
    expense_months_available: int = 3,
) -> FinancialSnapshot:
    """FR-10, 6.4: Full deterministic snapshot."""
    missing: list[str] = []

    # Income
    monthly_income, income_stale = compute_monthly_income(income_sources, income_txns, today)
    if monthly_income is None:
        missing.append("At least one income source or income transaction")

    # Expenses
    valid_expenses = [t for t in expense_txns if t.category.strip().lower() != "emi"]
    if not valid_expenses:
        missing.append("At least one expense transaction")

    if missing:
        return FinancialSnapshot(
            is_sufficient=False,
            missing_items=missing,
            monthly_income=Decimal("0"),
            essential_expenses=Decimal("0"),
            discretionary_expenses=Decimal("0"),
            total_expenses=Decimal("0"),
            debt_payments=Decimal("0"),
            net_cash_flow=Decimal("0"),
            savings_rate=Decimal("0"),
            dti=Decimal("0"),
            dti_level="low",
            net_worth=Decimal("0"),
            emergency_coverage_months=Decimal("0"),
            is_stale=False,
            stale_reasons=[],
        )

    # We know monthly_income is not None
    assert monthly_income is not None
    current_month_start = date(today.year, today.month, 1)
    window_start = _month_start_offset(current_month_start, -3)
    window_expenses = [
        t for t in valid_expenses if window_start <= t.txn_date < current_month_start
    ]
    scoped_expenses = window_expenses if window_expenses else valid_expenses
    distinct_months = len({(t.txn_date.year, t.txn_date.month) for t in scoped_expenses})
    months_count = max(1, min(expense_months_available, distinct_months))
    essential, discretionary = compute_expenses(scoped_expenses, months_count)
    total_expenses = essential + discretionary

    # Debt payments
    active_liabilities = [liab for liab in liabilities if liab.status == "active"]
    debt_payments = sum((liab.emi_amount for liab in active_liabilities), Decimal("0"))

    # Net cash flow
    net_cash_flow = monthly_income - essential - discretionary - debt_payments

    # Savings rate
    if monthly_income > Decimal("0"):
        savings_rate = round_cur((net_cash_flow / monthly_income) * Decimal("100"))
        dti = round_cur((debt_payments / monthly_income) * Decimal("100"))
    else:
        savings_rate = Decimal("0")
        dti = Decimal("0")

    if dti < Decimal("20"):
        dti_level = "low"
    elif dti <= Decimal("40"):
        dti_level = "moderate"
    else:
        dti_level = "high"

    # Net worth
    total_holdings = sum((h.current_value for h in holdings), Decimal("0"))
    total_debt = sum((liab.outstanding_principal for liab in active_liabilities), Decimal("0"))
    net_worth = total_holdings - total_debt

    # Emergency coverage
    emergency_reserves = sum(
        (h.current_value for h in holdings if h.is_emergency_reserve), Decimal("0")
    )
    monthly_burn = essential + debt_payments
    if monthly_burn > Decimal("0"):
        emergency_coverage_months = round_cur(emergency_reserves / monthly_burn)
    else:
        emergency_coverage_months = Decimal("999.00")

    # Stale tracking
    stale_reasons: list[str] = []
    if income_stale:
        stale_reasons.append("Income sources not updated in over 90 days")

    for liab in active_liabilities:
        if (today - liab.updated_at).days > 30:
            stale_reasons.append("Liabilities have entries older than 30 days")
            break

    for h in holdings:
        if (today - h.as_of_date).days > 30:
            stale_reasons.append("Holdings have entries older than 30 days")
            break

    if expense_txns:
        latest_txn = max(t.txn_date for t in expense_txns)
        if (today - latest_txn).days > 45:
            stale_reasons.append("No transaction recorded in over 45 days")

    return FinancialSnapshot(
        is_sufficient=True,
        missing_items=[],
        monthly_income=monthly_income,
        essential_expenses=essential,
        discretionary_expenses=discretionary,
        total_expenses=total_expenses,
        debt_payments=debt_payments,
        net_cash_flow=net_cash_flow,
        savings_rate=savings_rate,
        dti=dti,
        dti_level=dti_level,
        net_worth=net_worth,
        emergency_coverage_months=emergency_coverage_months,
        is_stale=len(stale_reasons) > 0,
        stale_reasons=stale_reasons,
    )
