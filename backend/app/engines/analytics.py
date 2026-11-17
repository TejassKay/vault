"""Pure Analytics Engine for Spending Insights.

Zero DB, network, or clock access. Pure Decimal arithmetic.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from app.engines.financial_engine import (
    ESSENTIAL_CATEGORIES,
    ExpenseInput,
    IncomeInput,
    _month_start_offset,
    round_cur,
)


def round_pct(val: Decimal) -> Decimal:
    """Round percentage to 2 decimal places half-up."""
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class AnalyticsHoldingInput:
    type: str
    current_value: Decimal


@dataclass(frozen=True)
class AnalyticsLiabilityInput:
    type: str
    outstanding_principal: Decimal
    emi_amount: Decimal
    status: str  # active, closed


@dataclass(frozen=True)
class CategoryBreakdownItem:
    category: str
    amount: Decimal
    share_percent: Decimal


@dataclass(frozen=True)
class CategoryBreakdown:
    items: list[CategoryBreakdownItem]
    total: Decimal


@dataclass(frozen=True)
class MonthlySeriesItem:
    month: str
    income: Decimal
    expenses: Decimal
    essential: Decimal
    discretionary: Decimal
    net: Decimal
    debt_payments: Decimal


@dataclass(frozen=True)
class CategoryTrendMonth:
    month: str
    totals: dict[str, Decimal]


@dataclass(frozen=True)
class CategoryTrend:
    categories: list[str]
    series: list[CategoryTrendMonth]


@dataclass(frozen=True)
class PacePoint:
    day: int
    cumulative: Decimal


@dataclass(frozen=True)
class SpendingPace:
    current_month: list[PacePoint]
    previous_month: list[PacePoint]
    comparison_day: int
    delta_at_day: Decimal


@dataclass(frozen=True)
class CategoryCompareItem:
    category: str
    amount: Decimal
    previous: Decimal
    delta: Decimal
    delta_percent: Decimal | None


@dataclass(frozen=True)
class HoldingCompositionItem:
    type: str
    value: Decimal
    share_percent: Decimal


@dataclass(frozen=True)
class LiabilityCompositionItem:
    type: str
    outstanding_principal: Decimal
    share_percent: Decimal


@dataclass(frozen=True)
class CompositionSummary:
    holdings_items: list[HoldingCompositionItem]
    holdings_total: Decimal
    liabilities_items: list[LiabilityCompositionItem]
    liabilities_total: Decimal


@dataclass(frozen=True)
class AnalyticsSummary:
    month: str
    months: int
    category_breakdown: CategoryBreakdown
    monthly_series: list[MonthlySeriesItem]
    category_trend: CategoryTrend
    spending_pace: SpendingPace
    compare: list[CategoryCompareItem]
    composition: CompositionSummary
    months_available: int
    has_data: bool


def _ym_str(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def _normalized_active_income(income_sources: list[IncomeInput]) -> Decimal | None:
    active_sources = [s for s in income_sources if s.is_active and s.frequency != "one_time"]
    if not active_sources:
        return None
    total = Decimal("0")
    for s in active_sources:
        if s.frequency == "monthly":
            total += s.amount
        elif s.frequency == "weekly":
            total += (s.amount * Decimal("52")) / Decimal("12")
        elif s.frequency == "yearly":
            total += s.amount / Decimal("12")
    return round_cur(total)


def _group_expenses_by_category(txns: list[ExpenseInput]) -> dict[str, Decimal]:
    """Sum non-EMI expense transactions by canonical category label."""
    by_key: dict[str, Decimal] = {}
    display_name: dict[str, str] = {}
    for t in txns:
        raw = t.category.strip()
        key = raw.lower()
        if key == "emi":
            continue
        if key not in display_name:
            display_name[key] = raw
        by_key[key] = by_key.get(key, Decimal("0")) + t.amount
    return {display_name[k]: v for k, v in by_key.items()}


def _build_pace_series(
    txns: list[ExpenseInput],
    year: int,
    month: int,
    max_day: int,
) -> list[PacePoint]:
    daily: dict[int, Decimal] = {}
    for t in txns:
        if t.category.strip().lower() == "emi":
            continue
        if t.txn_date.year == year and t.txn_date.month == month and t.txn_date.day <= max_day:
            daily[t.txn_date.day] = daily.get(t.txn_date.day, Decimal("0")) + t.amount

    points: list[PacePoint] = []
    running = Decimal("0")
    for day in range(1, max_day + 1):
        running += daily.get(day, Decimal("0"))
        points.append(PacePoint(day=day, cumulative=round_cur(running)))
    return points


def compute_analytics_summary(
    *,
    income_sources: list[IncomeInput],
    income_txns: list[ExpenseInput],
    expense_txns: list[ExpenseInput],
    liabilities: list[AnalyticsLiabilityInput],
    holdings: list[AnalyticsHoldingInput],
    selected_month_start: date,
    months: int,
    today: date,
) -> AnalyticsSummary:
    """Compute all spending insights metrics purely from in-memory inputs."""
    selected_ym = _ym_str(selected_month_start)
    prev_month_start = _month_start_offset(selected_month_start, -1)
    prev_ym = _ym_str(prev_month_start)

    # Distinct months with any transaction
    txn_months = {_ym_str(t.txn_date) for t in expense_txns} | {
        _ym_str(t.txn_date) for t in income_txns
    }
    months_available = len(txn_months)

    active_liabilities = [liab for liab in liabilities if liab.status == "active"]
    has_data = bool(expense_txns or income_txns or holdings or active_liabilities)

    # Partition transactions by YYYY-MM
    exp_by_month: dict[str, list[ExpenseInput]] = {}
    for t in expense_txns:
        ym = _ym_str(t.txn_date)
        exp_by_month.setdefault(ym, []).append(t)

    inc_by_month: dict[str, Decimal] = {}
    for t in income_txns:
        ym = _ym_str(t.txn_date)
        inc_by_month[ym] = inc_by_month.get(ym, Decimal("0")) + t.amount

    # 1. Category breakdown for selected month (EMI excluded)
    sel_cat_totals = _group_expenses_by_category(exp_by_month.get(selected_ym, []))
    sel_total = round_cur(sum(sel_cat_totals.values(), Decimal("0")))
    breakdown_items: list[CategoryBreakdownItem] = []
    if sel_total > Decimal("0"):
        for cat, amt in sorted(sel_cat_totals.items(), key=lambda kv: (-kv[1], kv[0].lower())):
            rounded_amt = round_cur(amt)
            share = round_pct((amt / sel_total) * Decimal("100"))
            breakdown_items.append(
                CategoryBreakdownItem(category=cat, amount=rounded_amt, share_percent=share)
            )
    category_breakdown = CategoryBreakdown(items=breakdown_items, total=sel_total)

    # 2. Monthly series: last N full months + selected month
    fixed_monthly_income = _normalized_active_income(income_sources)
    active_debt_payments = round_cur(
        sum((liab.emi_amount for liab in active_liabilities), Decimal("0"))
    )

    window_months: list[date] = [
        _month_start_offset(selected_month_start, -offset) for offset in range(months, -1, -1)
    ]
    monthly_series: list[MonthlySeriesItem] = []
    month_cat_maps: dict[str, dict[str, Decimal]] = {}

    for m_start in window_months:
        ym = _ym_str(m_start)
        m_txns = exp_by_month.get(ym, [])
        cat_map = _group_expenses_by_category(m_txns)
        month_cat_maps[ym] = cat_map

        essential = Decimal("0")
        discretionary = Decimal("0")
        for cat, amt in cat_map.items():
            if cat.strip().lower() in ESSENTIAL_CATEGORIES:
                essential += amt
            else:
                discretionary += amt

        essential_r = round_cur(essential)
        discretionary_r = round_cur(discretionary)
        expenses_r = round_cur(essential + discretionary)

        if fixed_monthly_income is not None:
            income_r = fixed_monthly_income
        else:
            income_r = round_cur(inc_by_month.get(ym, Decimal("0")))

        net_r = round_cur(income_r - expenses_r)
        monthly_series.append(
            MonthlySeriesItem(
                month=ym,
                income=income_r,
                expenses=expenses_r,
                essential=essential_r,
                discretionary=discretionary_r,
                net=net_r,
                debt_payments=active_debt_payments,
            )
        )

    # 3. Category trend: top 5 categories across the window, rest grouped as 'Other'
    window_cat_totals: dict[str, Decimal] = {}
    for cat_map in month_cat_maps.values():
        for cat, amt in cat_map.items():
            window_cat_totals[cat] = window_cat_totals.get(cat, Decimal("0")) + amt

    sorted_window_cats = [
        cat for cat, _ in sorted(window_cat_totals.items(), key=lambda kv: (-kv[1], kv[0].lower()))
    ]
    top_5 = sorted_window_cats[:5]
    has_other = len(sorted_window_cats) > 5
    trend_categories = [*top_5, "Other"] if has_other else list(top_5)

    trend_series: list[CategoryTrendMonth] = []
    for m_start in window_months:
        ym = _ym_str(m_start)
        cat_map = month_cat_maps[ym]
        totals: dict[str, Decimal] = {
            cat: round_cur(cat_map.get(cat, Decimal("0"))) for cat in top_5
        }
        if has_other:
            other_sum = sum(
                (amt for cat, amt in cat_map.items() if cat not in top_5),
                Decimal("0"),
            )
            totals["Other"] = round_cur(other_sum)
        trend_series.append(CategoryTrendMonth(month=ym, totals=totals))
    category_trend = CategoryTrend(categories=trend_categories, series=trend_series)

    # 4. Spending pace: cumulative spending by day for selected month vs previous month
    days_in_sel = calendar.monthrange(selected_month_start.year, selected_month_start.month)[1]
    days_in_prev = calendar.monthrange(prev_month_start.year, prev_month_start.month)[1]
    if selected_month_start.year == today.year and selected_month_start.month == today.month:
        sel_max_day = min(today.day, days_in_sel)
    else:
        sel_max_day = days_in_sel

    curr_pace = _build_pace_series(
        exp_by_month.get(selected_ym, []),
        selected_month_start.year,
        selected_month_start.month,
        sel_max_day,
    )
    prev_pace = _build_pace_series(
        exp_by_month.get(prev_ym, []),
        prev_month_start.year,
        prev_month_start.month,
        days_in_prev,
    )

    comparison_day = min(sel_max_day, days_in_prev)
    curr_at_day = (
        curr_pace[comparison_day - 1].cumulative if comparison_day >= 1 else Decimal("0.00")
    )
    prev_at_day = (
        prev_pace[comparison_day - 1].cumulative if comparison_day >= 1 else Decimal("0.00")
    )
    delta_at_day = round_cur(curr_at_day - prev_at_day)

    spending_pace = SpendingPace(
        current_month=curr_pace,
        previous_month=prev_pace,
        comparison_day=comparison_day,
        delta_at_day=delta_at_day,
    )

    # 5. Compare: selected month vs previous month per category
    prev_cat_totals = _group_expenses_by_category(exp_by_month.get(prev_ym, []))
    # Merge case-insensitively while preserving display names
    all_cats_by_lower: dict[str, str] = {}
    for cat in list(sel_cat_totals.keys()) + list(prev_cat_totals.keys()):
        all_cats_by_lower.setdefault(cat.lower(), cat)

    sel_lower = {k.lower(): v for k, v in sel_cat_totals.items()}
    prev_lower = {k.lower(): v for k, v in prev_cat_totals.items()}

    compare_items: list[CategoryCompareItem] = []
    for key, label in all_cats_by_lower.items():
        curr_amt = round_cur(sel_lower.get(key, Decimal("0")))
        prev_amt = round_cur(prev_lower.get(key, Decimal("0")))
        delta = round_cur(curr_amt - prev_amt)
        if prev_amt > Decimal("0"):
            delta_pct: Decimal | None = round_pct((delta / prev_amt) * Decimal("100"))
        else:
            delta_pct = None
        compare_items.append(
            CategoryCompareItem(
                category=label,
                amount=curr_amt,
                previous=prev_amt,
                delta=delta,
                delta_percent=delta_pct,
            )
        )
    compare_items.sort(key=lambda item: (-item.delta, -item.amount, item.category.lower()))

    # 6. Composition: holdings by type & active liabilities by type
    holdings_by_type: dict[str, Decimal] = {}
    for h in holdings:
        holdings_by_type[h.type] = holdings_by_type.get(h.type, Decimal("0")) + h.current_value
    holdings_total = round_cur(sum(holdings_by_type.values(), Decimal("0")))
    holdings_items: list[HoldingCompositionItem] = []
    if holdings_total > Decimal("0"):
        for h_type, val in sorted(holdings_by_type.items(), key=lambda kv: (-kv[1], kv[0])):
            holdings_items.append(
                HoldingCompositionItem(
                    type=h_type,
                    value=round_cur(val),
                    share_percent=round_pct((val / holdings_total) * Decimal("100")),
                )
            )

    liabs_by_type: dict[str, Decimal] = {}
    for liab in active_liabilities:
        liabs_by_type[liab.type] = (
            liabs_by_type.get(liab.type, Decimal("0")) + liab.outstanding_principal
        )
    liabilities_total = round_cur(sum(liabs_by_type.values(), Decimal("0")))
    liabilities_items: list[LiabilityCompositionItem] = []
    if liabilities_total > Decimal("0"):
        for l_type, principal in sorted(liabs_by_type.items(), key=lambda kv: (-kv[1], kv[0])):
            liabilities_items.append(
                LiabilityCompositionItem(
                    type=l_type,
                    outstanding_principal=round_cur(principal),
                    share_percent=round_pct((principal / liabilities_total) * Decimal("100")),
                )
            )

    composition = CompositionSummary(
        holdings_items=holdings_items,
        holdings_total=holdings_total,
        liabilities_items=liabilities_items,
        liabilities_total=liabilities_total,
    )

    return AnalyticsSummary(
        month=selected_ym,
        months=months,
        category_breakdown=category_breakdown,
        monthly_series=monthly_series,
        category_trend=category_trend,
        spending_pace=spending_pace,
        compare=compare_items,
        composition=composition,
        months_available=months_available,
        has_data=has_data,
    )
