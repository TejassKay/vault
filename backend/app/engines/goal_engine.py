"""FR-9, FR-27, 6.5: Goal Engine pure calculations.

Calculates:
- Progress percentage
- Whole months remaining
- Required monthly contribution across scenarios (0%, 2%, 4%, 6%, 7%, 10%)
  using formula:
    when r == 0: (target - saved) / n
    when r > 0:  max(0, (target - saved * (1+i)^n) * i / ((1+i)^n - 1)) where i = r/12

Zero DB, network, or clock access.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal


def round_cur(val: Decimal) -> Decimal:
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class GoalScenarioResult:
    rate_percent: Decimal
    required_monthly_contribution: Decimal


@dataclass(frozen=True)
class GoalProjection:
    goal_id: int
    title: str
    target_amount: Decimal
    saved_amount: Decimal
    target_date: date
    months_left: int
    progress_percent: Decimal
    planning_contribution: Decimal  # 0% scenario
    scenarios: list[GoalScenarioResult]
    disclaimer: str = "Projections are estimates and are not guaranteed."


def compute_months_left(today: date, target_date: date) -> int:
    """Whole months from today to target_date, minimum 1."""
    months = (target_date.year - today.year) * 12 + (target_date.month - today.month)
    return max(1, months)


def compute_required_contribution(
    target: Decimal,
    saved: Decimal,
    months_n: int,
    annual_rate_percent: Decimal,
) -> Decimal:
    """Calculate required monthly contribution.

    When r is 0: (target - saved) / n
    When r > 0: max(0, (target - saved * (1+i)^n) * i / ((1+i)^n - 1)) where i = r/12
    """
    if target <= saved:
        return Decimal("0.00")

    n = Decimal(str(months_n))

    if annual_rate_percent == Decimal("0"):
        return round_cur((target - saved) / n)

    # Convert to float for exponential calculation then back to Decimal
    r = float(annual_rate_percent) / 100.0
    i = r / 12.0
    target_f = float(target)
    saved_f = float(saved)
    n_f = float(months_n)

    compounded = (1.0 + i) ** n_f
    numerator = (target_f - saved_f * compounded) * i
    denominator = compounded - 1.0

    if denominator <= 0:
        return Decimal("0.00")

    result_f = max(0.0, numerator / denominator)
    return round_cur(Decimal(str(result_f)))


def compute_goal_projection(
    goal_id: int,
    title: str,
    target_amount: Decimal,
    saved_amount: Decimal,
    target_date: date,
    today: date,
) -> GoalProjection:
    """FR-9, FR-27, 6.5: Full goal projection with scenario rates based on horizon."""
    months_left = compute_months_left(today, target_date)

    if target_amount > Decimal("0"):
        progress = min(
            Decimal("100.00"), round_cur((saved_amount / target_amount) * Decimal("100"))
        )
    else:
        progress = Decimal("100.00")

    # Scenario rates by horizon (6.5)
    # <= 36 months: 0%, 2%, 4%
    # 37 to 60 months: 0%, 4%, 7%
    # > 60 months: 0%, 6%, 10%
    if months_left <= 36:
        rates = [Decimal("0"), Decimal("2"), Decimal("4")]
    elif months_left <= 60:
        rates = [Decimal("0"), Decimal("4"), Decimal("7")]
    else:
        rates = [Decimal("0"), Decimal("6"), Decimal("10")]

    scenarios = [
        GoalScenarioResult(
            rate_percent=rate,
            required_monthly_contribution=compute_required_contribution(
                target_amount, saved_amount, months_left, rate
            ),
        )
        for rate in rates
    ]

    planning_contrib = scenarios[0].required_monthly_contribution  # 0% scenario

    return GoalProjection(
        goal_id=goal_id,
        title=title,
        target_amount=target_amount,
        saved_amount=saved_amount,
        target_date=target_date,
        months_left=months_left,
        progress_percent=progress,
        planning_contribution=planning_contrib,
        scenarios=scenarios,
    )
