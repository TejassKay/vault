"""FR-21, FR-29, Spec 6.7: Pure Investment Capacity Engine.

Calculates:
- Surplus (net cash flow)
- Planning contributions of active goals (0% scenario)
- Emergency reserve top-up needed to reach 6 months of coverage
- Remaining investable margin
- Capacity with 10% volatility buffer
- Hard gates: EMERGENCY_FUND_LOW (coverage < 3) and HIGH_INTEREST_DEBT (rate >= 12%)
- Step-by-step breakdown and reason codes

Zero DB, network, or clock access. Pure Decimal arithmetic.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.engines.financial_engine import (
    FinancialSnapshot,
    HoldingInput,
    LiabilityInput,
    round_cur,
)
from app.engines.goal_engine import compute_months_left, compute_required_contribution


@dataclass(frozen=True)
class GoalInput:
    target_amount: Decimal
    saved_amount: Decimal
    target_date: date
    status: str = "active"


@dataclass(frozen=True)
class CapacityStep:
    step_number: int
    name: str
    value: Decimal | None
    description: str


@dataclass(frozen=True)
class InvestmentCapacityResult:
    status: str  # "ok", "blocked", "insufficient_data"
    capacity: Decimal | None
    capacity_if_clear: Decimal | None
    surplus: Decimal | None
    goal_contribution: Decimal | None
    emergency_top_up: Decimal | None
    remaining: Decimal | None
    steps: list[CapacityStep]
    reason_codes: list[str]
    missing_items: list[str]
    assumptions: list[str]


def compute_investment_capacity(
    snapshot: FinancialSnapshot,
    goals: list[GoalInput],
    liabilities: list[LiabilityInput],
    holdings: list[HoldingInput],
    today: date,
) -> InvestmentCapacityResult:
    """FR-21, FR-29, Spec 6.7: Deterministic investment capacity with visible breakdown."""
    if not snapshot.is_sufficient:
        return InvestmentCapacityResult(
            status="insufficient_data",
            capacity=None,
            capacity_if_clear=None,
            surplus=None,
            goal_contribution=None,
            emergency_top_up=None,
            remaining=None,
            steps=[],
            reason_codes=[],
            missing_items=snapshot.missing_items,
            assumptions=[],
        )

    # 1. surplus = net cash flow
    surplus = snapshot.net_cash_flow

    # 2. goal_contribution = sum of planning contributions of active goals (0% scenario)
    active_goals = [g for g in goals if g.status == "active"]
    goal_contribution = Decimal("0.00")
    for g in active_goals:
        months_left = compute_months_left(today, g.target_date)
        req = compute_required_contribution(
            target=g.target_amount,
            saved=g.saved_amount,
            months_n=months_left,
            annual_rate_percent=Decimal("0"),
        )
        goal_contribution += req
    goal_contribution = round_cur(goal_contribution)

    # 3. emergency_top_up
    monthly_burn = snapshot.essential_expenses + snapshot.debt_payments
    reserves = sum((h.current_value for h in holdings if h.is_emergency_reserve), Decimal("0"))

    if snapshot.emergency_coverage_months < Decimal("6.00"):
        target_reserves = Decimal("6") * monthly_burn
        shortfall = max(Decimal("0"), target_reserves - reserves)
        emergency_top_up = round_cur(shortfall / Decimal("12"))
    else:
        emergency_top_up = Decimal("0.00")

    # 4. remaining = surplus - goal_contribution - emergency_top_up
    remaining = surplus - goal_contribution - emergency_top_up

    # 5. capacity_if_clear = max(0, remaining) * 0.90 (10% buffer)
    zero = Decimal("0.00")
    if remaining > zero:
        capacity_if_clear = round_cur(remaining * Decimal("0.90"))
    else:
        capacity_if_clear = zero

    # 6. Hard gates
    reason_codes: list[str] = []
    if snapshot.emergency_coverage_months < Decimal("3.00"):
        reason_codes.append("EMERGENCY_FUND_LOW")

    active_liabilities = [liab for liab in liabilities if liab.status == "active"]
    if any(liab.interest_rate >= Decimal("12.00") for liab in active_liabilities):
        reason_codes.append("HIGH_INTEREST_DEBT")

    if reason_codes:
        status = "blocked"
        capacity = Decimal("0.00")
    else:
        status = "ok"
        capacity = capacity_if_clear

    # 7. Ordered breakdown steps
    steps = [
        CapacityStep(
            step_number=1,
            name="Net Cash Flow Surplus",
            value=surplus,
            description="Monthly income minus essential, discretionary, and debt payments",
        ),
        CapacityStep(
            step_number=2,
            name="Goal Contributions",
            value=goal_contribution,
            description="Monthly allocation required for active goals under conservative 0% return",
        ),
        CapacityStep(
            step_number=3,
            name="Emergency Reserve Top-Up",
            value=emergency_top_up,
            description="Monthly top-up to achieve 6 months of liquid emergency coverage within 12 months",
        ),
        CapacityStep(
            step_number=4,
            name="Remaining Margin",
            value=remaining,
            description="Surplus after deducting active goal contributions and emergency fund top-up",
        ),
        CapacityStep(
            step_number=5,
            name="Capacity (with 10% Volatility Buffer)",
            value=capacity_if_clear,
            description="Remaining margin multiplied by 0.90 to retain a 10% cash flow buffer",
        ),
    ]

    if status == "blocked":
        steps.append(
            CapacityStep(
                step_number=6,
                name="Safety Priority Hold",
                value=Decimal("0.00"),
                description=f"New investing paused at ₹0.00 until safety priorities are met: {', '.join(reason_codes)}",
            )
        )

    assumptions = [
        "Conservative 0% return assumed for goal contributions",
        "Target emergency fund is 6 months of essential living expenses and debt payments",
        "10% cash flow volatility buffer retained before committing to investments",
    ]

    return InvestmentCapacityResult(
        status=status,
        capacity=capacity,
        capacity_if_clear=capacity_if_clear,
        surplus=surplus,
        goal_contribution=goal_contribution,
        emergency_top_up=emergency_top_up,
        remaining=remaining,
        steps=steps,
        reason_codes=reason_codes,
        missing_items=[],
        assumptions=assumptions,
    )
