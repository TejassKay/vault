"""FR-21 to FR-26, FR-29: Risk Questionnaire, Investment Capacity, and Advisor Router."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.engines.advisor_engine import (
    ADVISOR_DISCLAIMER,
    build_advisor_plan,
)
from app.engines.financial_engine import (
    ExpenseInput,
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
    RISK_QUESTIONS,
    compute_capacity_level,
    compute_effective_level,
    compute_tolerance_level,
    score_questionnaire,
)
from app.models.goal import Goal
from app.models.holding import Holding
from app.models.income_source import IncomeSource
from app.models.liability import Liability
from app.models.recommendation import Recommendation
from app.models.risk_profile import RiskProfile
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.advisor import (
    CapacityStepSchema,
    InvestmentCapacityResponse,
    QuestionOptionSchema,
    RecommendationListResponse,
    RecommendationResponse,
    RecommendationUpdate,
    RiskProfileCreate,
    RiskProfileResponse,
    RiskQuestionnaireResponse,
    RiskQuestionSchema,
)
from app.services.advisor_explainer import explain_plan_recommendations

router = APIRouter(tags=["advisor"])


def _load_user_financial_data(
    db: Session, user_id: int, today: date
) -> tuple[Any, list[GoalInput], list[LiabilityInput], list[HoldingInput], list[ExpenseInput]]:
    """Helper to load and convert DB entities into pure engine inputs."""
    sources = db.query(IncomeSource).filter(IncomeSource.user_id == user_id).all()
    inc_inputs = [
        IncomeInput(
            amount=s.amount,
            frequency=s.frequency,
            is_active=s.is_active,
            updated_at=s.updated_at.date() if s.updated_at else today,
        )
        for s in sources
    ]

    txns = db.query(Transaction).filter(Transaction.user_id == user_id).all()
    exp_inputs = [
        ExpenseInput(amount=t.amount, category=t.category, txn_date=t.txn_date)
        for t in txns
        if t.type == "expense"
    ]
    inc_txn_inputs = [
        ExpenseInput(amount=t.amount, category=t.category, txn_date=t.txn_date)
        for t in txns
        if t.type == "income"
    ]

    liabs = db.query(Liability).filter(Liability.user_id == user_id).all()
    liab_inputs = [
        LiabilityInput(
            outstanding_principal=item.outstanding_principal,
            emi_amount=item.emi_amount,
            interest_rate=item.interest_rate,
            status=item.status,
            updated_at=item.updated_at.date() if item.updated_at else today,
        )
        for item in liabs
    ]

    holdings = db.query(Holding).filter(Holding.user_id == user_id).all()
    hold_inputs = [
        HoldingInput(
            current_value=h.current_value,
            is_emergency_reserve=h.is_emergency_reserve,
            as_of_date=h.as_of_date,
        )
        for h in holdings
    ]

    goals = db.query(Goal).filter(Goal.user_id == user_id).all()
    goal_inputs = [
        GoalInput(
            target_amount=g.target_amount,
            saved_amount=g.saved_amount,
            target_date=g.target_date,
            status=g.status,
        )
        for g in goals
    ]

    snapshot = compute_financial_snapshot(
        income_sources=inc_inputs,
        income_txns=inc_txn_inputs,
        expense_txns=exp_inputs,
        liabilities=liab_inputs,
        holdings=hold_inputs,
        today=today,
    )

    discretionary_txns = [
        t for t in exp_inputs if t.category.strip().lower() not in {
            "rent", "groceries", "utilities", "transport", "health", "education", "insurance", "emi"
        }
    ]

    return snapshot, goal_inputs, liab_inputs, hold_inputs, discretionary_txns


# ---------------------------------------------------------------------------
# Risk Questionnaire (FR-22)
# ---------------------------------------------------------------------------


@router.get("/risk-questionnaire", response_model=RiskQuestionnaireResponse)
def get_risk_questionnaire() -> RiskQuestionnaireResponse:
    """Return the 8 standardized risk questionnaire questions and options."""
    questions = [
        RiskQuestionSchema(
            id=q.id,
            text=q.text,
            options=[QuestionOptionSchema(text=opt.text, score=opt.score) for opt in q.options],
        )
        for q in RISK_QUESTIONS
    ]
    return RiskQuestionnaireResponse(questions=questions)


@router.post("/risk-profile", response_model=RiskProfileResponse, status_code=status.HTTP_201_CREATED)
def submit_risk_profile(
    data: RiskProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RiskProfileResponse:
    """Submit 8 answers, calculate score, tolerance, capacity, and effective risk level."""
    today = date.today()
    snapshot, _, _, _, _ = _load_user_financial_data(db, current_user.user_id, today)

    score = score_questionnaire(data.answers)
    tolerance = compute_tolerance_level(score)

    if snapshot.is_sufficient:
        capacity_lvl = compute_capacity_level(snapshot.emergency_coverage_months, snapshot.dti)
    else:
        # If insufficient data, capacity is conservative/low
        capacity_lvl = "low"

    effective = compute_effective_level(tolerance, capacity_lvl)

    profile = RiskProfile(
        user_id=current_user.user_id,
        answers=data.answers,
        score=score,
        tolerance_level=tolerance,
        capacity_level=capacity_lvl,
        effective_level=effective,
        assessed_at=datetime.now(UTC),
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    return RiskProfileResponse.model_validate(profile)


@router.get("/risk-profile", response_model=RiskProfileResponse | None)
def get_risk_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RiskProfileResponse | None:
    """Get the user's latest assessed risk profile."""
    profile = (
        db.query(RiskProfile)
        .filter(RiskProfile.user_id == current_user.user_id)
        .order_by(RiskProfile.assessed_at.desc())
        .first()
    )
    if not profile:
        return None
    return RiskProfileResponse.model_validate(profile)


# ---------------------------------------------------------------------------
# Investment Capacity (FR-21, FR-29)
# ---------------------------------------------------------------------------


@router.get("/investment-capacity", response_model=InvestmentCapacityResponse)
def get_investment_capacity(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InvestmentCapacityResponse:
    """FR-21, FR-29: Step-by-step breakdown of monthly investment capacity."""
    today = date.today()
    snapshot, goals, liabs, holdings, _ = _load_user_financial_data(db, current_user.user_id, today)

    capacity_res = compute_investment_capacity(
        snapshot=snapshot,
        goals=goals,
        liabilities=liabs,
        holdings=holdings,
        today=today,
    )

    return InvestmentCapacityResponse(
        status=capacity_res.status,
        capacity=capacity_res.capacity,
        capacity_if_clear=capacity_res.capacity_if_clear,
        surplus=capacity_res.surplus,
        goal_contribution=capacity_res.goal_contribution,
        emergency_top_up=capacity_res.emergency_top_up,
        remaining=capacity_res.remaining,
        steps=[
            CapacityStepSchema(
                step_number=s.step_number,
                name=s.name,
                value=s.value,
                description=s.description,
            )
            for s in capacity_res.steps
        ],
        reason_codes=capacity_res.reason_codes,
        missing_items=capacity_res.missing_items,
        assumptions=capacity_res.assumptions,
    )


# ---------------------------------------------------------------------------
# Advisor & Recommendations (FR-23, FR-24, FR-25, FR-26)
# ---------------------------------------------------------------------------


@router.post("/recommendations/generate", response_model=RecommendationListResponse)
def generate_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecommendationListResponse:
    """FR-23, 24, 25: Build prioritized recommendations, explain them via LLM/template, save to DB."""
    today = date.today()
    snapshot, goals, liabs, holdings, disc_txns = _load_user_financial_data(
        db, current_user.user_id, today
    )

    capacity_res = compute_investment_capacity(
        snapshot=snapshot,
        goals=goals,
        liabilities=liabs,
        holdings=holdings,
        today=today,
    )

    # Latest risk profile
    latest_profile = (
        db.query(RiskProfile)
        .filter(RiskProfile.user_id == current_user.user_id)
        .order_by(RiskProfile.assessed_at.desc())
        .first()
    )
    effective_risk = latest_profile.effective_level if latest_profile else "moderate"

    # Build deterministic plan
    plan = build_advisor_plan(
        snapshot=snapshot,
        capacity=capacity_res,
        goals=goals,
        liabilities=liabs,
        risk_effective_level=effective_risk,
        discretionary_txns=disc_txns,
    )

    # Explain recommendations (LLM or template fallback with number-guard)
    explain_plan_recommendations(plan.recommendations)

    # Persist recommendations to DB
    batch_time = datetime.now(UTC)
    saved_entities: list[Recommendation] = []
    for item in plan.recommendations:
        rec = Recommendation(
            user_id=current_user.user_id,
            priority_rank=item.priority_rank,
            rec_type=item.rec_type,
            action=item.action,
            reason=item.reason,
            assumptions=item.assumptions,
            risks=item.risks,
            alternatives=item.alternatives,
            review_trigger=item.review_trigger,
            inputs_snapshot=item.inputs_snapshot,
            engine_version=item.engine_version,
            explanation_text=item.explanation_text,
            explanation_source=item.explanation_source,
            status=item.status,
            created_at=batch_time,
        )
        db.add(rec)
        saved_entities.append(rec)

    db.commit()
    for rec in saved_entities:
        db.refresh(rec)

    response_items = [RecommendationResponse.model_validate(r) for r in saved_entities]
    return RecommendationListResponse(
        recommendations=response_items,
        disclaimer=plan.disclaimer,
    )


@router.get("/recommendations", response_model=RecommendationListResponse)
def get_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecommendationListResponse:
    """Return latest recommendations for current user with statutory disclaimer."""
    # Fetch latest created recommendations
    # We find the most recent generation batch or all active
    subquery = (
        db.query(Recommendation.created_at)
        .filter(Recommendation.user_id == current_user.user_id)
        .order_by(Recommendation.created_at.desc())
        .first()
    )

    if not subquery:
        return RecommendationListResponse(
            recommendations=[],
            disclaimer=ADVISOR_DISCLAIMER,
        )

    latest_timestamp = subquery[0]
    threshold = latest_timestamp - timedelta(seconds=2)
    records = (
        db.query(Recommendation)
        .filter(
            Recommendation.user_id == current_user.user_id,
            Recommendation.created_at >= threshold,
        )
        .order_by(Recommendation.priority_rank.asc())
        .all()
    )

    response_items = [RecommendationResponse.model_validate(r) for r in records]
    return RecommendationListResponse(
        recommendations=response_items,
        disclaimer=ADVISOR_DISCLAIMER,
    )


@router.patch("/recommendations/{recommendation_id}", response_model=RecommendationResponse)
def update_recommendation_status(
    recommendation_id: int,
    data: RecommendationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecommendationResponse:
    """FR-26: User can accept, edit or reject a recommendation; stores the decision."""
    rec = (
        db.query(Recommendation)
        .filter(
            Recommendation.recommendation_id == recommendation_id,
            Recommendation.user_id == current_user.user_id,
        )
        .first()
    )
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation with ID {recommendation_id} not found",
        )

    rec.status = data.status
    rec.decided_at = datetime.now(UTC)
    db.commit()
    db.refresh(rec)

    return RecommendationResponse.model_validate(rec)
