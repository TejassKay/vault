"""FR-23, FR-24, Spec 6.9: Pure Advisor Rule Engine.

Applies prioritized deterministic rules to generate explainable recommendations:
  0: DATA_INSUFFICIENT
  1: NEGATIVE_CASH_FLOW
  2: HIGH_INTEREST_DEBT
  3: EMERGENCY_FUND_LOW
  4: EMERGENCY_FUND_BUILD
  5: GOALS_UNDERFUNDED
  6: INVEST_BY_CATEGORY
  7: REVIEW_SCHEDULE

Priority order, maximum 6 returned.
Zero DB, network, or clock access. Pure logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.engines.financial_engine import (
    ExpenseInput,
    FinancialSnapshot,
    LiabilityInput,
    round_cur,
)
from app.engines.investment_engine import GoalInput, InvestmentCapacityResult
from app.engines.risk_engine import compute_allocation

ADVISOR_DISCLAIMER = (
    "Vault provides general educational decision support based on the information you entered. "
    "It is not investment advice and does not recommend specific products. "
    "Projections are estimates, not guarantees. Consider consulting a SEBI-registered investment adviser."
)


@dataclass
class RecommendationPlanItem:
    priority_rank: int
    rec_type: str
    action: str
    reason: str
    assumptions: list[str]
    risks: list[str]
    alternatives: list[str]
    review_trigger: str
    inputs_snapshot: dict[str, Any]
    engine_version: str = "1.0"
    explanation_text: str | None = None
    explanation_source: str | None = None  # "llm" or "template"
    status: str = "proposed"


@dataclass
class AdvisorPlan:
    is_sufficient: bool
    recommendations: list[RecommendationPlanItem]
    disclaimer: str = ADVISOR_DISCLAIMER


def build_advisor_plan(
    snapshot: FinancialSnapshot,
    capacity: InvestmentCapacityResult,
    goals: list[GoalInput],
    liabilities: list[LiabilityInput],
    risk_effective_level: str = "moderate",
    discretionary_txns: list[ExpenseInput] | None = None,
) -> AdvisorPlan:
    """Spec 6.9: Apply rules in strict priority order, returning at most 6 items."""
    # Rank 0: DATA_INSUFFICIENT
    if not snapshot.is_sufficient:
        item = RecommendationPlanItem(
            priority_rank=0,
            rec_type="DATA_INSUFFICIENT",
            action="Add missing financial records to unlock personalized recommendations",
            reason=(
                f"Your profile is missing required baseline data: {', '.join(snapshot.missing_items)}. "
                "Vault requires recorded income and regular expenses to evaluate cash flow and capacity."
            ),
            assumptions=["Complete baseline inputs are necessary before calculating surplus or debt ratios"],
            risks=["Acting on incomplete financial visibility creates unexpected cash shortfalls"],
            alternatives=["Enter at least one regular income source and expense transactions from the last month"],
            review_trigger="Immediately upon entering income and expense records",
            inputs_snapshot={"missing_items": snapshot.missing_items},
            engine_version="1.0",
        )
        return AdvisorPlan(is_sufficient=False, recommendations=[item])

    candidates: list[RecommendationPlanItem] = []
    active_liabilities = [liab for liab in liabilities if liab.status == "active"]

    # Base snapshot dict for audit provenance
    base_snapshot: dict[str, Any] = {
        "monthly_income": float(snapshot.monthly_income),
        "essential_expenses": float(snapshot.essential_expenses),
        "discretionary_expenses": float(snapshot.discretionary_expenses),
        "debt_payments": float(snapshot.debt_payments),
        "net_cash_flow": float(snapshot.net_cash_flow),
        "savings_rate": float(snapshot.savings_rate),
        "dti": float(snapshot.dti),
        "net_worth": float(snapshot.net_worth),
        "emergency_coverage_months": float(snapshot.emergency_coverage_months),
        "risk_effective_level": risk_effective_level,
    }
    if capacity.capacity is not None:
        base_snapshot["investment_capacity"] = float(capacity.capacity)

    # -------------------------------------------------------------------------
    # Rank 1: NEGATIVE_CASH_FLOW (Net cash flow is 0 or less)
    # -------------------------------------------------------------------------
    if snapshot.net_cash_flow <= Decimal("0.00"):
        top_cats: list[str] = []
        if discretionary_txns:
            # Aggregate discretionary spending by category
            cat_sums: dict[str, Decimal] = {}
            for t in discretionary_txns:
                cat_sums[t.category] = cat_sums.get(t.category, Decimal("0")) + t.amount
            sorted_cats = sorted(cat_sums.items(), key=lambda x: x[1], reverse=True)[:3]
            top_cats = [f"{cat} (₹{amt:,.2f})" for cat, amt in sorted_cats]

        cat_str = (
            f"The largest discretionary categories are: {', '.join(top_cats)}."
            if top_cats
            else "Review non-essential subscriptions and entertainment spending."
        )

        candidates.append(
            RecommendationPlanItem(
                priority_rank=1,
                rec_type="NEGATIVE_CASH_FLOW",
                action="Review discretionary expenses to eliminate monthly cash deficit",
                reason=(
                    f"Your monthly expenses and debt obligations exceed your income by ₹{abs(snapshot.net_cash_flow):,.2f}. "
                    f"{cat_str}"
                ),
                assumptions=["Discretionary expenses can be adjusted without compromising essential necessities"],
                risks=["Persistent monthly deficits force reliance on high-cost revolving debt or emergency depletion"],
                alternatives=[
                    "Pause non-essential monthly subscriptions",
                    "Establish a hard weekly discretionary spending limit",
                    "Explore opportunities for supplementary variable income",
                ],
                review_trigger="Monthly expense reconciliation or income adjustment",
                inputs_snapshot={
                    **base_snapshot,
                    "net_cash_flow": float(snapshot.net_cash_flow),
                },
                engine_version="1.0",
            )
        )

    # -------------------------------------------------------------------------
    # Rank 2: HIGH_INTEREST_DEBT (Any active liability rate >= 12%)
    # -------------------------------------------------------------------------
    high_interest_liabs = [liab for liab in active_liabilities if liab.interest_rate >= Decimal("12.00")]
    if high_interest_liabs:
        highest_rate = max(liab.interest_rate for liab in high_interest_liabs)
        total_high_principal = sum((liab.outstanding_principal for liab in high_interest_liabs), Decimal("0"))
        candidates.append(
            RecommendationPlanItem(
                priority_rank=2,
                rec_type="HIGH_INTEREST_DEBT",
                action="Accelerate repayment of high-interest debt prior to investing",
                reason=(
                    f"You have active liabilities with interest rates reaching {highest_rate:.2f}%, "
                    f"totalling ₹{total_high_principal:,.2f} in outstanding principal. Guaranteed interest savings "
                    "from debt repayment consistently exceed uncertain market investment yields."
                ),
                assumptions=[
                    "Prepayment is permitted by the lender without prohibitive exit penalties",
                    "Existing emergency reserve covers immediate obligations",
                ],
                risks=[
                    "Early foreclosure or prepayment penalties might apply; review loan terms",
                    "Diverting liquid funds may limit near-term flexibility",
                ],
                alternatives=[
                    "Refinance or consolidate balances to a lower interest rate loan",
                    "Snowball method: repay the smallest balance first for psychological momentum",
                ],
                review_trigger="Full repayment or refinancing of high-interest loan",
                inputs_snapshot={
                    **base_snapshot,
                    "highest_interest_rate": float(highest_rate),
                    "total_high_interest_principal": float(total_high_principal),
                },
                engine_version="1.0",
            )
        )

    # -------------------------------------------------------------------------
    # Rank 3: EMERGENCY_FUND_LOW (Coverage below 3 months)
    # -------------------------------------------------------------------------
    monthly_burn = snapshot.essential_expenses + snapshot.debt_payments
    if snapshot.emergency_coverage_months < Decimal("3.00"):
        target_3m = round_cur(Decimal("3") * monthly_burn)
        target_6m = round_cur(Decimal("6") * monthly_burn)
        current_reserves = round_cur(snapshot.emergency_coverage_months * monthly_burn)
        shortfall_3m = max(Decimal("0.00"), target_3m - current_reserves)

        candidates.append(
            RecommendationPlanItem(
                priority_rank=3,
                rec_type="EMERGENCY_FUND_LOW",
                action="Build liquid emergency reserves to cover at least 3 months of essential obligations",
                reason=(
                    f"Your liquid emergency reserves cover {snapshot.emergency_coverage_months:.2f} months "
                    f"(₹{current_reserves:,.2f}), below the critical safety baseline of 3 months (₹{target_3m:,.2f}). "
                    f"Direct available cash flow to close the ₹{shortfall_3m:,.2f} safety gap before investing."
                ),
                assumptions=[
                    f"Monthly essential living and debt burn remains at ₹{monthly_burn:,.2f}",
                    "Surplus cash flow will be retained in liquid bank accounts or liquid funds",
                ],
                risks=["Unplanned medical, appliance, or income disruptions could force costly borrowing"],
                alternatives=[
                    "Direct 100% of monthly surplus into a dedicated liquid emergency fund",
                    "Reallocate existing non-locked holdings to liquid reserves",
                ],
                review_trigger=f"Emergency coverage reaches 3 months (₹{target_3m:,.2f})",
                inputs_snapshot={
                    **base_snapshot,
                    "target_3m": float(target_3m),
                    "target_6m": float(target_6m),
                    "shortfall_3m": float(shortfall_3m),
                },
                engine_version="1.0",
            )
        )

    # -------------------------------------------------------------------------
    # Rank 4: EMERGENCY_FUND_BUILD (Coverage between 3 and 6 months)
    # -------------------------------------------------------------------------
    elif snapshot.emergency_coverage_months < Decimal("6.00"):
        target_6m = round_cur(Decimal("6") * monthly_burn)
        current_reserves = round_cur(snapshot.emergency_coverage_months * monthly_burn)
        top_up_mo = capacity.emergency_top_up or round_cur((target_6m - current_reserves) / Decimal("12"))

        candidates.append(
            RecommendationPlanItem(
                priority_rank=4,
                rec_type="EMERGENCY_FUND_BUILD",
                action="Gradually expand emergency reserves to target 6 months alongside goals",
                reason=(
                    f"Your emergency reserves cover {snapshot.emergency_coverage_months:.2f} months. While above "
                    f"the 3-month safety minimum, saving ₹{top_up_mo:,.2f}/month alongside your goals will reach "
                    f"the comprehensive 6-month safety reserve of ₹{target_6m:,.2f} over the next 12 months."
                ),
                assumptions=["Monthly essential expenses remain stable", "Steady monthly income continues uninterrupted"],
                risks=["Extended economic or employment disruptions lasting beyond 3 months"],
                alternatives=[
                    "Park emergency reserves in high-yield liquid mutual funds or sweep-in fixed deposits",
                    "Balance top-up with priority goal timelines",
                ],
                review_trigger=f"Emergency coverage reaches 6 months (₹{target_6m:,.2f})",
                inputs_snapshot={
                    **base_snapshot,
                    "target_6m": float(target_6m),
                    "monthly_top_up": float(top_up_mo),
                },
                engine_version="1.0",
            )
        )

    # -------------------------------------------------------------------------
    # Rank 5: GOALS_UNDERFUNDED (Sum of goal contributions exceeds cash flow)
    # -------------------------------------------------------------------------
    total_goal_contrib = capacity.goal_contribution or Decimal("0.00")
    if total_goal_contrib > snapshot.net_cash_flow and snapshot.net_cash_flow > Decimal("0.00"):
        shortfall = total_goal_contrib - snapshot.net_cash_flow
        candidates.append(
            RecommendationPlanItem(
                priority_rank=5,
                rec_type="GOALS_UNDERFUNDED",
                action="Rebalance savings goals target dates or contributions to prevent cash deficits",
                reason=(
                    f"Your active goals require ₹{total_goal_contrib:,.2f}/month in contributions, which exceeds your "
                    f"monthly net cash flow of ₹{snapshot.net_cash_flow:,.2f} by ₹{shortfall:,.2f}/month."
                ),
                assumptions=["Goals are scheduled under 0% conservative return projections"],
                risks=["Attempting to fund all goals simultaneously will cause cash deficits or missed obligations"],
                alternatives=[
                    "Extend target dates for lower-priority goals by 6 to 12 months",
                    "Reduce target amounts for non-essential goals",
                    "Focus contributions on high-priority goals sequentially",
                ],
                review_trigger="Goal deadline extension or increase in monthly surplus",
                inputs_snapshot={
                    **base_snapshot,
                    "total_goal_contributions": float(total_goal_contrib),
                    "shortfall": float(shortfall),
                },
                engine_version="1.0",
            )
        )

    # -------------------------------------------------------------------------
    # Rank 6: INVEST_BY_CATEGORY (Capacity status ok and capacity > 0)
    # -------------------------------------------------------------------------
    if capacity.status == "ok" and capacity.capacity is not None and capacity.capacity > Decimal("0.00"):
        alloc = compute_allocation(risk_effective_level, horizon_months=61)
        breakdown_parts: list[str] = []
        breakdown_dict: dict[str, float] = {}

        for cat, pct in alloc.items():
            if pct > 0:
                amt = round_cur((capacity.capacity * Decimal(str(pct))) / Decimal("100"))
                breakdown_parts.append(f"{cat}: ₹{amt:,.2f} ({pct}%)")
                breakdown_dict[cat] = float(amt)

        breakdown_text = "; ".join(breakdown_parts)

        candidates.append(
            RecommendationPlanItem(
                priority_rank=6,
                rec_type="INVEST_BY_CATEGORY",
                action=f"Deploy sustainable investment capacity of ₹{capacity.capacity:,.2f}/month across asset categories",
                reason=(
                    f"Based on your {risk_effective_level} risk profile and investment capacity of "
                    f"₹{capacity.capacity:,.2f}/month (after retaining a 10% volatility buffer and goal deductions), "
                    f"allocate by asset class: {breakdown_text}."
                ),
                assumptions=[
                    "Market returns fluctuate over time; historical returns do not guarantee future performance",
                    "10% volatility buffer protects against unexpected cash flow variance",
                ],
                risks=[
                    "Market volatility in equity funds",
                    "Interest rate and inflation risk in fixed income instruments",
                ],
                alternatives=[
                    "Adjust category weightings based on individual goal horizons",
                    "Start with recurring monthly SIP allocations in diversified index funds",
                ],
                review_trigger="Annual portfolio rebalancing, milestone event, or risk profile reassessment",
                inputs_snapshot={
                    **base_snapshot,
                    "sustainable_capacity": float(capacity.capacity),
                    "category_allocation": breakdown_dict,
                },
                engine_version="1.0",
            )
        )

    # -------------------------------------------------------------------------
    # Rank 7: REVIEW_SCHEDULE (Always present)
    # -------------------------------------------------------------------------
    candidates.append(
        RecommendationPlanItem(
            priority_rank=7,
            rec_type="REVIEW_SCHEDULE",
            action="Maintain regular financial review schedule to keep allocations aligned",
            reason=(
                "Your financial situation evolves as income changes, loans are repaid, and goal dates approach. "
                "Periodic reviews ensure your emergency coverage and investment capacity remain optimized."
            ),
            assumptions=["Financial variables change across career and life milestones"],
            risks=["Outdated assumptions can lead to under-insured emergencies or suboptimal asset allocations"],
            alternatives=[
                "Set a quarterly calendar reminder for checking financial health",
                "Re-run advisor after any salary change or new loan disbursement",
            ],
            review_trigger="Income change, new liability, goal target date within 6 months, or stale data (>30 days)",
            inputs_snapshot=base_snapshot,
            engine_version="1.0",
        )
    )

    # Maximum 6 returned in priority order
    final_items = candidates[:6]
    # Re-index priority_rank 1..N
    for idx, item in enumerate(final_items, start=1):
        item.priority_rank = idx

    return AdvisorPlan(is_sufficient=True, recommendations=final_items)
