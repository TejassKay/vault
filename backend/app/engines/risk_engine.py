"""FR-22, Spec 6.8: Pure Risk Engine and Asset Allocation.

Calculates:
- 8-question questionnaire scoring (8 to 32)
- Risk tolerance level: conservative (8-16), moderate (17-24), aggressive (25-32)
- Risk capacity level from snapshot: low (coverage < 3 or DTI > 40), medium (coverage < 6 or DTI > 25), high otherwise
- Effective risk level: lower of tolerance and capacity cap
- Allocation percentages across categories by horizon and effective level
- Goal investment category suggestions by horizon

Zero DB, network, or clock access. Pure logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

LEVEL_ORDER = {
    "conservative": 1,
    "moderate": 2,
    "aggressive": 3,
}

ORDER_TO_LEVEL = {
    1: "conservative",
    2: "moderate",
    3: "aggressive",
}

CATEGORY_EQUITY = "Diversified equity or index funds"
CATEGORY_DEBT = "Debt funds, fixed deposits or government securities"
CATEGORY_GOLD = "Gold"
CATEGORY_LIQUID = "Liquid funds or savings account"


@dataclass(frozen=True)
class QuestionOption:
    text: str
    score: int  # 1 to 4


@dataclass(frozen=True)
class RiskQuestion:
    id: str
    text: str
    options: list[QuestionOption]


RISK_QUESTIONS: list[RiskQuestion] = [
    RiskQuestion(
        id="q1_horizon",
        text="What is your primary investment horizon?",
        options=[
            QuestionOption("Less than 1 year", 1),
            QuestionOption("1 to 3 years", 2),
            QuestionOption("3 to 5 years", 3),
            QuestionOption("More than 5 years", 4),
        ],
    ),
    RiskQuestion(
        id="q2_market_fall",
        text="How would you react if your investment portfolio fell by 20% in a few months?",
        options=[
            QuestionOption("Panic and sell everything immediately to prevent further loss", 1),
            QuestionOption("Sell part of the portfolio to cut risk", 2),
            QuestionOption("Hold steady and wait for market recovery", 3),
            QuestionOption("View it as a buying opportunity and invest more", 4),
        ],
    ),
    RiskQuestion(
        id="q3_experience",
        text="What is your prior experience with financial markets and investing?",
        options=[
            QuestionOption("No experience; complete beginner", 1),
            QuestionOption("Basic experience with bank savings, deposits, or PF", 2),
            QuestionOption("Moderate experience with mutual funds and some equities", 3),
            QuestionOption("Extensive experience with active equities and market cycles", 4),
        ],
    ),
    RiskQuestion(
        id="q4_income_stability",
        text="How predictable and stable is your monthly income?",
        options=[
            QuestionOption("Highly irregular or uncertain", 1),
            QuestionOption("Somewhat variable or gig/contract based", 2),
            QuestionOption("Stable salary or dependable business cash flow", 3),
            QuestionOption("Very secure with high certainty (e.g. tenured or government role)", 4),
        ],
    ),
    RiskQuestion(
        id="q5_dependents",
        text="How many individuals are financially dependent on your income?",
        options=[
            QuestionOption("3 or more dependents", 1),
            QuestionOption("2 dependents", 2),
            QuestionOption("1 dependent", 3),
            QuestionOption("No dependents (financially independent)", 4),
        ],
    ),
    RiskQuestion(
        id="q6_essentials_share",
        text="What portion of your monthly take-home income is spent on unavoidable living expenses?",
        options=[
            QuestionOption("More than 75%", 1),
            QuestionOption("50% to 75%", 2),
            QuestionOption("25% to 50%", 3),
            QuestionOption("Less than 25%", 4),
        ],
    ),
    RiskQuestion(
        id="q7_purpose",
        text="What is your main financial objective for this invested capital?",
        options=[
            QuestionOption("Capital preservation and safety first", 1),
            QuestionOption("Beat inflation with steady, modest growth", 2),
            QuestionOption("Balanced wealth accumulation over the medium-to-long term", 3),
            QuestionOption("Aggressive long-term wealth multiplication", 4),
        ],
    ),
    RiskQuestion(
        id="q8_volatility_comfort",
        text="How comfortable are you with daily or weekly fluctuations in your portfolio balance?",
        options=[
            QuestionOption("Very uncomfortable; causes anxiety or sleep loss", 1),
            QuestionOption("Somewhat uncomfortable with noticeable dips", 2),
            QuestionOption("Comfortable accepting normal economic cycles and fluctuations", 3),
            QuestionOption("Very comfortable; prioritize high long-term returns over stability", 4),
        ],
    ),
]


def score_questionnaire(answers: dict[str, Any]) -> int:
    """Calculate total score from 8 answers.

    Accepts answers dict where keys are question IDs (or q1..q8, 1..8) and values are 1-4.
    Returns total score between 8 and 32.
    """
    total = 0
    for q in RISK_QUESTIONS:
        val = answers.get(q.id)
        if val is None:
            # Try short key like "q1", or question number
            idx = q.id.split("_")[0]  # "q1"
            val = answers.get(idx)
        if val is None:
            # Default to middle value if missing (score 2)
            val = 2
        try:
            score = int(val)
        except (ValueError, TypeError):
            score = 2
        score = max(1, min(4, score))
        total += score

    return max(8, min(32, total))


def compute_tolerance_level(score: int) -> str:
    """Spec 6.8: 8–16 conservative; 17–24 moderate; 25–32 aggressive."""
    if score <= 16:
        return "conservative"
    if score <= 24:
        return "moderate"
    return "aggressive"


def compute_capacity_level(emergency_coverage_months: Decimal, dti: Decimal) -> str:
    """Spec 6.8:

    low if coverage is below 3 or DTI is over 40;
    medium if coverage is below 6 or DTI is over 25;
    otherwise high.
    """
    if emergency_coverage_months < Decimal("3.00") or dti > Decimal("40.00"):
        return "low"
    if emergency_coverage_months < Decimal("6.00") or dti > Decimal("25.00"):
        return "medium"
    return "high"


def compute_effective_level(tolerance_level: str, capacity_level: str) -> str:
    """Spec 6.8:

    Capacity caps the level:
    - low caps at conservative
    - medium caps at moderate
    - high caps at aggressive
    Effective level is the lower of tolerance and capacity cap.
    """
    capacity_caps = {
        "low": "conservative",
        "medium": "moderate",
        "high": "aggressive",
    }
    cap = capacity_caps.get(capacity_level.lower(), "moderate")

    tol_order = LEVEL_ORDER.get(tolerance_level.lower(), 2)
    cap_order = LEVEL_ORDER.get(cap, 2)

    effective_order = min(tol_order, cap_order)
    return ORDER_TO_LEVEL[effective_order]


def compute_allocation(effective_level: str, horizon_months: int = 61) -> dict[str, int]:
    """Spec 6.8: Percent allocation (equity / debt / gold / liquid).

    Horizon over 60 months:
      conservative: 20/60/10/10
      moderate:     50/35/10/5
      aggressive:   70/20/10/0

    Horizon 37 to 60 months:
      Move 20 points of equity to debt (minimum equity 0):
      conservative: 0/80/10/10
      moderate:     30/55/10/5
      aggressive:   50/40/10/0

    Horizon 36 months or less:
      debt 50, liquid 50, equity 0, gold 0.
    """
    level = effective_level.lower()
    if level not in LEVEL_ORDER:
        level = "moderate"

    if horizon_months <= 36:
        return {
            CATEGORY_EQUITY: 0,
            CATEGORY_DEBT: 50,
            CATEGORY_GOLD: 0,
            CATEGORY_LIQUID: 50,
        }

    if horizon_months <= 60:
        if level == "conservative":
            return {
                CATEGORY_EQUITY: 0,
                CATEGORY_DEBT: 80,
                CATEGORY_GOLD: 10,
                CATEGORY_LIQUID: 10,
            }
        if level == "moderate":
            return {
                CATEGORY_EQUITY: 30,
                CATEGORY_DEBT: 55,
                CATEGORY_GOLD: 10,
                CATEGORY_LIQUID: 5,
            }
        # aggressive
        return {
            CATEGORY_EQUITY: 50,
            CATEGORY_DEBT: 40,
            CATEGORY_GOLD: 10,
            CATEGORY_LIQUID: 0,
        }

    # Horizon > 60 months
    if level == "conservative":
        return {
            CATEGORY_EQUITY: 20,
            CATEGORY_DEBT: 60,
            CATEGORY_GOLD: 10,
            CATEGORY_LIQUID: 10,
        }
    if level == "moderate":
        return {
            CATEGORY_EQUITY: 50,
            CATEGORY_DEBT: 35,
            CATEGORY_GOLD: 10,
            CATEGORY_LIQUID: 5,
        }
    # aggressive
    return {
        CATEGORY_EQUITY: 70,
        CATEGORY_DEBT: 20,
        CATEGORY_GOLD: 10,
        CATEGORY_LIQUID: 0,
    }


def suggest_goal_allocation(horizon_months: int, effective_level: str) -> str:
    """Spec 6.8: Goal suggestions by horizon."""
    if horizon_months <= 12:
        return "Liquid funds or savings account"
    if horizon_months <= 36:
        return "Liquid funds, debt funds or fixed deposits"
    if horizon_months <= 60:
        return "Debt funds or fixed deposits with at most 30% diversified equity"
    return f"Asset allocation matching your effective risk level ({effective_level})"
