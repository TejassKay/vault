"""Unit tests for Phase 4: InvestmentEngine, RiskEngine, AdvisorEngine, and AdvisorExplainer.

Covers:
- FR-21: Investment capacity calculation with step-by-step breakdown
- FR-22: 8-question risk scoring, tolerance, capacity, and effective level
- FR-23: Prioritized recommendations
- FR-24: Explainable recommendation structure (action, reason, assumptions, risks, alternatives, review_trigger)
- FR-25: LLM explanation number-guard and template fallback
- FR-26: Recommendation decision handling
- FR-29: Insufficient data handling (no numbers returned)
- Golden test cases from Spec 6.6
- Engine coverage >= 90% (NFR-10)
"""

from datetime import date
from decimal import Decimal

from app.engines.advisor_engine import (
    ADVISOR_DISCLAIMER,
    build_advisor_plan,
)
from app.engines.financial_engine import (
    FinancialSnapshot,
    HoldingInput,
    IncomeInput,
    LiabilityInput,
    compute_financial_snapshot,
)
from app.engines.investment_engine import (
    GoalInput,
    compute_investment_capacity,
)
from app.engines.risk_engine import (
    CATEGORY_DEBT,
    CATEGORY_EQUITY,
    CATEGORY_GOLD,
    CATEGORY_LIQUID,
    compute_allocation,
    compute_capacity_level,
    compute_effective_level,
    compute_tolerance_level,
    score_questionnaire,
    suggest_goal_allocation,
)
from app.services.advisor_explainer import (
    collect_allowed_numbers,
    explain_plan_recommendations,
    number_guard,
)


def _build_golden_scenario_inputs():
    today = date(2026, 11, 13)
    incomes = [
        IncomeInput(
            amount=Decimal("85000"),
            frequency="monthly",
            is_active=True,
            updated_at=date(2026, 11, 1),
        )
    ]
    # Aug, Sep, Oct expenses
    from app.engines.financial_engine import ExpenseInput

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

    goals = [
        GoalInput(
            target_amount=Decimal("500000"),
            saved_amount=Decimal("50000"),
            target_date=date(2028, 11, 13),  # 24 months
            status="active",
        )
    ]

    return today, incomes, expenses, liabilities, goals


# ---------------------------------------------------------------------------
# FR-21 & Golden Spec 6.6: Investment Capacity
# ---------------------------------------------------------------------------


def test_fr21_golden_scenario_a_capacity() -> None:
    """Spec 6.6 Scenario A:

    Reserve: 45,000 -> Emergency coverage: 1.07 months
    Emergency top-up: 17,250
    Investment capacity: 0 (blocked with EMERGENCY_FUND_LOW)
    """
    today, incomes, expenses, liabilities, goals = _build_golden_scenario_inputs()
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
    )

    cap_a = compute_investment_capacity(
        snapshot=snap_a,
        goals=goals,
        liabilities=liabilities,
        holdings=holdings_a,
        today=today,
    )

    assert cap_a.status == "blocked"
    assert cap_a.capacity == Decimal("0.00")
    assert cap_a.surplus == Decimal("35000.00")
    assert cap_a.goal_contribution == Decimal("18750.00")
    assert cap_a.emergency_top_up == Decimal("17250.00")
    assert cap_a.remaining == Decimal("-1000.00")
    assert cap_a.capacity_if_clear == Decimal("0.00")
    assert "EMERGENCY_FUND_LOW" in cap_a.reason_codes
    assert len(cap_a.steps) >= 5


def test_fr21_golden_scenario_b_capacity() -> None:
    """Spec 6.6 Scenario B:

    Reserve: 2,60,000 -> Emergency coverage: 6.19 months
    Emergency top-up: 0
    Investment capacity: 14,625.00 (status: ok)
    Calculation: 35,000 - 18,750 - 0 = 16,250; 16,250 * 0.90 = 14,625.00
    """
    today, incomes, expenses, liabilities, goals = _build_golden_scenario_inputs()
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
    )

    cap_b = compute_investment_capacity(
        snapshot=snap_b,
        goals=goals,
        liabilities=liabilities,
        holdings=holdings_b,
        today=today,
    )

    assert cap_b.status == "ok"
    assert cap_b.capacity == Decimal("14625.00")
    assert cap_b.capacity_if_clear == Decimal("14625.00")
    assert cap_b.surplus == Decimal("35000.00")
    assert cap_b.goal_contribution == Decimal("18750.00")
    assert cap_b.emergency_top_up == Decimal("0.00")
    assert cap_b.remaining == Decimal("16250.00")
    assert cap_b.reason_codes == []


def test_fr21_hard_gate_high_interest_debt() -> None:
    """Spec 6.7: Any active liability with interest_rate >= 12% sets capacity to 0 and blocks."""
    today, incomes, expenses, _, goals = _build_golden_scenario_inputs()
    holdings_b = [
        HoldingInput(
            current_value=Decimal("260000"), is_emergency_reserve=True, as_of_date=date(2026, 11, 1)
        ),
    ]
    # High interest loan at 14.5%
    liabs_high = [
        LiabilityInput(
            outstanding_principal=Decimal("50000"),
            emi_amount=Decimal("3000"),
            interest_rate=Decimal("14.50"),
            status="active",
            updated_at=date(2026, 11, 1),
        )
    ]

    snap = compute_financial_snapshot(
        income_sources=incomes,
        income_txns=[],
        expense_txns=expenses,
        liabilities=liabs_high,
        holdings=holdings_b,
        today=today,
    )

    cap = compute_investment_capacity(
        snapshot=snap,
        goals=goals,
        liabilities=liabs_high,
        holdings=holdings_b,
        today=today,
    )

    assert cap.status == "blocked"
    assert cap.capacity == Decimal("0.00")
    assert "HIGH_INTEREST_DEBT" in cap.reason_codes
    assert cap.capacity_if_clear > Decimal("0.00")


def test_fr29_insufficient_data_returns_no_number() -> None:
    """FR-29, Spec 6.7: When data is insufficient, return status insufficient_data and no number."""
    today = date(2026, 11, 13)
    empty_snap = FinancialSnapshot(
        is_sufficient=False,
        missing_items=["At least one income source"],
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

    cap = compute_investment_capacity(
        snapshot=empty_snap,
        goals=[],
        liabilities=[],
        holdings=[],
        today=today,
    )

    assert cap.status == "insufficient_data"
    assert cap.capacity is None
    assert cap.capacity_if_clear is None
    assert "At least one income source" in cap.missing_items


# ---------------------------------------------------------------------------
# FR-22 & Spec 6.8: Risk Engine & Asset Allocation
# ---------------------------------------------------------------------------


def test_fr22_risk_questionnaire_scoring() -> None:
    """Spec 6.8: 8 questions scored 1 to 4 -> score 8 to 32."""
    # Min score
    min_answers = {f"q{i}": 1 for i in range(1, 9)}
    min_score = score_questionnaire(min_answers)
    assert min_score == 8
    assert compute_tolerance_level(min_score) == "conservative"

    # Max score
    max_answers = {f"q{i}": 4 for i in range(1, 9)}
    max_score = score_questionnaire(max_answers)
    assert max_score == 32
    assert compute_tolerance_level(max_score) == "aggressive"

    # Mid score
    mid_answers = {"q1": 2, "q2": 3, "q3": 2, "q4": 3, "q5": 2, "q6": 3, "q7": 2, "q8": 3}
    mid_score = score_questionnaire(mid_answers)
    assert mid_score == 20
    assert compute_tolerance_level(mid_score) == "moderate"


def test_fr22_risk_capacity_and_lower_of_rule() -> None:
    """Spec 6.8: Capacity levels & effective level lower-of rule."""
    # Low capacity: coverage < 3 or DTI > 40
    assert compute_capacity_level(Decimal("1.50"), Decimal("10.00")) == "low"
    assert compute_capacity_level(Decimal("8.00"), Decimal("45.00")) == "low"

    # Medium capacity: coverage < 6 or DTI > 25
    assert compute_capacity_level(Decimal("4.50"), Decimal("15.00")) == "medium"
    assert compute_capacity_level(Decimal("7.00"), Decimal("30.00")) == "medium"

    # High capacity
    assert compute_capacity_level(Decimal("6.50"), Decimal("15.00")) == "high"

    # Lower-of rule: tolerance vs capacity cap
    # Aggressive tolerance + Low capacity -> Capped at Conservative
    assert compute_effective_level("aggressive", "low") == "conservative"
    # Aggressive tolerance + Medium capacity -> Capped at Moderate
    assert compute_effective_level("aggressive", "medium") == "moderate"
    # Aggressive tolerance + High capacity -> Aggressive
    assert compute_effective_level("aggressive", "high") == "aggressive"
    # Conservative tolerance + High capacity -> Conservative
    assert compute_effective_level("conservative", "high") == "conservative"


def test_fr22_asset_allocation_tables() -> None:
    """Spec 6.8: Allocation tables by horizon and effective level."""
    # Horizon > 60 months
    c_long = compute_allocation("conservative", horizon_months=72)
    assert c_long[CATEGORY_EQUITY] == 20
    assert c_long[CATEGORY_DEBT] == 60
    assert c_long[CATEGORY_GOLD] == 10
    assert c_long[CATEGORY_LIQUID] == 10

    m_long = compute_allocation("moderate", horizon_months=72)
    assert m_long[CATEGORY_EQUITY] == 50
    assert m_long[CATEGORY_DEBT] == 35
    assert m_long[CATEGORY_GOLD] == 10
    assert m_long[CATEGORY_LIQUID] == 5

    a_long = compute_allocation("aggressive", horizon_months=72)
    assert a_long[CATEGORY_EQUITY] == 70
    assert a_long[CATEGORY_DEBT] == 20
    assert a_long[CATEGORY_GOLD] == 10
    assert a_long[CATEGORY_LIQUID] == 0

    # Horizon 37 to 60 months (shift 20 points of equity to debt)
    m_mid = compute_allocation("moderate", horizon_months=48)
    assert m_mid[CATEGORY_EQUITY] == 30
    assert m_mid[CATEGORY_DEBT] == 55
    assert m_mid[CATEGORY_GOLD] == 10
    assert m_mid[CATEGORY_LIQUID] == 5

    c_mid = compute_allocation("conservative", horizon_months=48)
    assert c_mid[CATEGORY_EQUITY] == 0  # min equity 0
    assert c_mid[CATEGORY_DEBT] == 80
    assert c_mid[CATEGORY_GOLD] == 10
    assert c_mid[CATEGORY_LIQUID] == 10

    # Horizon <= 36 months (debt 50, liquid 50)
    short = compute_allocation("aggressive", horizon_months=24)
    assert short[CATEGORY_DEBT] == 50
    assert short[CATEGORY_LIQUID] == 50
    assert short[CATEGORY_EQUITY] == 0
    assert short[CATEGORY_GOLD] == 0

    # Goal suggestion labels
    assert suggest_goal_allocation(6, "moderate") == "Liquid funds or savings account"
    assert suggest_goal_allocation(24, "moderate") == "Liquid funds, debt funds or fixed deposits"


# ---------------------------------------------------------------------------
# FR-23, FR-24 & Spec 6.9: Advisor Priority Rules
# ---------------------------------------------------------------------------


def test_fr23_golden_scenario_a_top_rec_emergency_fund() -> None:
    """Spec 6.6 & 6.9: Scenario A top recommendation must be Build emergency fund."""
    today, incomes, expenses, liabilities, goals = _build_golden_scenario_inputs()
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
    )
    cap_a = compute_investment_capacity(
        snapshot=snap_a,
        goals=goals,
        liabilities=liabilities,
        holdings=holdings_a,
        today=today,
    )

    plan = build_advisor_plan(
        snapshot=snap_a,
        capacity=cap_a,
        goals=goals,
        liabilities=liabilities,
        risk_effective_level="moderate",
    )

    assert plan.is_sufficient is True
    assert len(plan.recommendations) > 0
    top_rec = plan.recommendations[0]
    assert top_rec.rec_type == "EMERGENCY_FUND_LOW"
    assert "emergency" in top_rec.action.lower()
    assert top_rec.review_trigger is not None
    assert top_rec.engine_version == "1.0"
    assert plan.disclaimer == ADVISOR_DISCLAIMER


def test_fr23_golden_scenario_b_top_rec_invest_by_category() -> None:
    """Spec 6.6 & 6.9: Scenario B top recommendation must be Invest by category."""
    today, incomes, expenses, liabilities, goals = _build_golden_scenario_inputs()
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
    )
    cap_b = compute_investment_capacity(
        snapshot=snap_b,
        goals=goals,
        liabilities=liabilities,
        holdings=holdings_b,
        today=today,
    )

    plan = build_advisor_plan(
        snapshot=snap_b,
        capacity=cap_b,
        goals=goals,
        liabilities=liabilities,
        risk_effective_level="moderate",
    )

    assert plan.is_sufficient is True
    top_rec = plan.recommendations[0]
    assert top_rec.rec_type == "INVEST_BY_CATEGORY"
    assert "14,625" in top_rec.action
    assert plan.disclaimer == ADVISOR_DISCLAIMER


def test_fr23_max_six_recommendations_and_fields() -> None:
    """Spec 6.9: Maximum 6 recommendations returned; all required explainability fields present."""
    today, incomes, expenses, liabilities, goals = _build_golden_scenario_inputs()
    holdings_b = [
        HoldingInput(
            current_value=Decimal("260000"), is_emergency_reserve=True, as_of_date=date(2026, 11, 1)
        ),
    ]
    snap = compute_financial_snapshot(
        income_sources=incomes,
        income_txns=[],
        expense_txns=expenses,
        liabilities=liabilities,
        holdings=holdings_b,
        today=today,
    )
    cap = compute_investment_capacity(
        snapshot=snap,
        goals=goals,
        liabilities=liabilities,
        holdings=holdings_b,
        today=today,
    )

    plan = build_advisor_plan(
        snapshot=snap,
        capacity=cap,
        goals=goals,
        liabilities=liabilities,
        risk_effective_level="moderate",
    )

    assert len(plan.recommendations) <= 6
    for rec in plan.recommendations:
        assert rec.action
        assert rec.reason
        assert isinstance(rec.assumptions, list) and len(rec.assumptions) > 0
        assert isinstance(rec.risks, list) and len(rec.risks) > 0
        assert isinstance(rec.alternatives, list) and len(rec.alternatives) > 0
        assert rec.review_trigger


# ---------------------------------------------------------------------------
# FR-25 & Spec 6.10: Number-Guard and Template Fallback
# ---------------------------------------------------------------------------


def test_fr25_number_guard_accepts_faithful_text() -> None:
    """Spec 6.10: Number guard accepts text containing only numbers from plan JSON."""
    plan_data = {
        "monthly_income": 85000.0,
        "net_cash_flow": 35000.0,
        "investment_capacity": 14625.0,
        "savings_rate": 41.18,
    }
    allowed = collect_allowed_numbers(plan_data)

    faithful_text = (
        "Based on your net cash flow of ₹35,000 and savings rate of 41.18%, "
        "your sustainable monthly investment capacity is ₹14,625.00."
    )
    is_valid, msg = number_guard(faithful_text, allowed)
    assert is_valid is True, msg


def test_fr25_number_guard_rejects_invented_number() -> None:
    """Spec 6.10: Number guard rejects text containing numbers not present in plan JSON."""
    plan_data = {
        "monthly_income": 85000.0,
        "net_cash_flow": 35000.0,
    }
    allowed = collect_allowed_numbers(plan_data)

    hallucinated_text = "Based on your income of ₹85,000, you can easily save ₹99,999 next month."
    is_valid, msg = number_guard(hallucinated_text, allowed)
    assert is_valid is False
    assert "99999" in msg or "not present" in msg


def test_fr25_number_guard_rejects_forbidden_words() -> None:
    """Spec 6.10: Number guard rejects guaranteed, risk-free, assured returns, will earn."""
    allowed = {1000.0, 5000.0}

    for forbidden in ["guaranteed", "risk-free", "assured returns", "will earn"]:
        bad_text = f"You will get a {forbidden} amount of ₹1,000."
        is_valid, msg = number_guard(bad_text, allowed)
        assert is_valid is False
        assert forbidden in msg.lower()


def test_fr25_explainer_template_fallback_execution() -> None:
    """Spec 6.10: Template explanation fills in on fallback and sets explanation_source = template."""
    today, incomes, expenses, liabilities, goals = _build_golden_scenario_inputs()
    holdings_b = [
        HoldingInput(
            current_value=Decimal("260000"), is_emergency_reserve=True, as_of_date=date(2026, 11, 1)
        ),
    ]
    snap = compute_financial_snapshot(
        income_sources=incomes,
        income_txns=[],
        expense_txns=expenses,
        liabilities=liabilities,
        holdings=holdings_b,
        today=today,
    )
    cap = compute_investment_capacity(
        snapshot=snap,
        goals=goals,
        liabilities=liabilities,
        holdings=holdings_b,
        today=today,
    )
    plan = build_advisor_plan(
        snapshot=snap,
        capacity=cap,
        goals=goals,
        liabilities=liabilities,
        risk_effective_level="moderate",
    )

    explain_plan_recommendations(plan.recommendations)

    for rec in plan.recommendations:
        assert rec.explanation_text
        assert rec.explanation_source in ("template", "llm")
