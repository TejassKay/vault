"""FR-8, 6.11: Budgeting nudge pure calculation.

Compare month-to-date expenses (excluding EMI) with the previous full month.
Projected = month-to-date / days elapsed * days in month.
If MTD > previous: alert exceeded.
Else if projected > 110% of previous: alert on track to exceed, naming largest increase category.
Otherwise show no nudge. Neutral, non-shaming tone.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal


def round_cur(val: Decimal) -> Decimal:
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class BudgetNudge:
    should_show: bool
    message: str | None
    projected_amount: Decimal | None
    previous_month_amount: Decimal | None
    largest_category_increase: str | None


def compute_budget_nudge(
    current_month_expenses: list[tuple[Decimal, str]],  # (amount, category)
    previous_month_expenses: list[tuple[Decimal, str]],
    today: date,
) -> BudgetNudge:
    """FR-8, 6.11: Generate month-on-month budgeting nudge."""
    # Filter out EMI
    mtd_items = [(amt, cat) for amt, cat in current_month_expenses if cat.strip().lower() != "emi"]
    prev_items = [
        (amt, cat) for amt, cat in previous_month_expenses if cat.strip().lower() != "emi"
    ]

    total_prev = sum((amt for amt, _ in prev_items), Decimal("0"))
    total_mtd = sum((amt for amt, _ in mtd_items), Decimal("0"))

    if total_prev <= Decimal("0"):
        return BudgetNudge(
            should_show=False,
            message=None,
            projected_amount=None,
            previous_month_amount=None,
            largest_category_increase=None,
        )

    days_in_month = calendar.monthrange(today.year, today.month)[1]
    days_elapsed = max(1, today.day)

    projected = round_cur((total_mtd / Decimal(str(days_elapsed))) * Decimal(str(days_in_month)))

    # Category breakdowns
    mtd_by_cat: dict[str, Decimal] = {}
    for amt, cat in mtd_items:
        c = cat.strip()
        mtd_by_cat[c] = mtd_by_cat.get(c, Decimal("0")) + amt

    prev_by_cat: dict[str, Decimal] = {}
    for amt, cat in prev_items:
        c = cat.strip()
        prev_by_cat[c] = prev_by_cat.get(c, Decimal("0")) + amt

    # Find category with largest absolute increase
    largest_cat = None
    largest_increase = Decimal("0")
    for cat, amt in mtd_by_cat.items():
        prev_amt = prev_by_cat.get(cat, Decimal("0"))
        increase = amt - prev_amt
        if increase > largest_increase:
            largest_increase = increase
            largest_cat = cat

    # Case 1: MTD already exceeds previous month
    if total_mtd > total_prev:
        msg = (
            f"Your spending this month (₹{total_mtd:,.2f}) has exceeded last month's total "
            f"(₹{total_prev:,.2f})."
        )
        if largest_cat:
            msg += f" The largest increase is in {largest_cat}."
        return BudgetNudge(
            should_show=True,
            message=msg,
            projected_amount=projected,
            previous_month_amount=total_prev,
            largest_category_increase=largest_cat,
        )

    # Case 2: Projected spending exceeds 110% of previous month
    threshold = total_prev * Decimal("1.10")
    if projected > threshold:
        msg = (
            f"At your current pace, projected spending is ₹{projected:,.2f}, which is higher than "
            f"last month's ₹{total_prev:,.2f}."
        )
        if largest_cat:
            msg += f" The highest pace increase is in {largest_cat}."
        return BudgetNudge(
            should_show=True,
            message=msg,
            projected_amount=projected,
            previous_month_amount=total_prev,
            largest_category_increase=largest_cat,
        )

    return BudgetNudge(
        should_show=False,
        message=None,
        projected_amount=projected,
        previous_month_amount=total_prev,
        largest_category_increase=None,
    )
