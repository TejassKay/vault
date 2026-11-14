"""FR-11, FR-12, FR-28: Overview, Dashboard, Timeline, and Demo Seed Router."""

from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.engines.advisor_engine import build_advisor_plan
from app.engines.dashboard_aggregator import (
    build_dashboard_summary,
    build_timeline_events,
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
from app.models.appliance import Appliance, Service
from app.models.goal import Goal
from app.models.holding import Holding
from app.models.income_source import IncomeSource
from app.models.liability import Liability
from app.models.recommendation import Recommendation
from app.models.risk_profile import RiskProfile
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.dashboard import (
    DashboardAssetAlertSchema,
    DashboardGoalSummarySchema,
    DashboardObligationSchema,
    DashboardResponse,
    DemoSeedRequest,
    DemoSeedResponse,
    TimelineEventSchema,
    TimelineResponse,
)
from app.schemas.finance import FinancialSnapshotResponse
from app.seed.demo_user import seed_demo_user

router = APIRouter(tags=["overview"])


def _extract_user_context(
    db: Session, user_id: int, today: date
) -> tuple[
    Any,
    list[GoalInput],
    list[LiabilityInput],
    list[HoldingInput],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    """Load DB records for a user into engine-ready structures."""
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
            outstanding_principal=liab.outstanding_principal,
            emi_amount=liab.emi_amount,
            interest_rate=liab.interest_rate,
            status=liab.status,
            updated_at=liab.updated_at.date() if liab.updated_at else today,
        )
        for liab in liabs
    ]
    liab_dicts = [
        {
            "liability_id": liab.liability_id,
            "type": liab.type,
            "lender_name": liab.lender_name,
            "emi_amount": float(liab.emi_amount),
            "due_day": liab.due_day,
            "status": liab.status,
        }
        for liab in liabs
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
    goal_dicts = [
        {
            "goal_id": g.goal_id,
            "title": g.title,
            "target_amount": float(g.target_amount),
            "saved_amount": float(g.saved_amount),
            "target_date": g.target_date,
            "status": g.status,
        }
        for g in goals
    ]

    appliances = db.query(Appliance).filter(Appliance.user_id == user_id).all()
    appliance_dicts = [
        {
            "appliance_id": a.appliance_id,
            "product_name": a.product_name,
            "brand": a.brand,
            "price": float(a.price) if a.price else None,
            "estimated_value": float(a.estimated_value) if a.estimated_value else None,
            "warranty_end_date": a.warranty_end_date,
        }
        for a in appliances
    ]

    services = (
        db.query(Service)
        .join(Appliance, Service.appliance_id == Appliance.appliance_id)
        .filter(Appliance.user_id == user_id)
        .all()
    )
    service_dicts = [
        {
            "service_id": s.service_id,
            "appliance_id": s.appliance_id,
            "product_name": s.appliance.product_name if s.appliance else "Appliance",
            "due_date": s.due_date,
            "status": s.status,
            "cost": float(s.cost) if s.cost else None,
            "guidance_label": s.guidance_label,
            "note": s.note,
        }
        for s in services
    ]

    snapshot = compute_financial_snapshot(
        income_sources=inc_inputs,
        income_txns=inc_txn_inputs,
        expense_txns=exp_inputs,
        liabilities=liab_inputs,
        holdings=hold_inputs,
        today=today,
    )

    return (
        snapshot,
        goal_inputs,
        liab_inputs,
        hold_inputs,
        liab_dicts,
        goal_dicts,
        appliance_dicts,
        service_dicts,
    )


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardResponse:
    """FR-11, FR-18, FR-28: Complete unified financial & asset dashboard."""
    today = date.today()
    (
        snapshot,
        goal_inputs,
        liab_inputs,
        hold_inputs,
        liab_dicts,
        goal_dicts,
        appliance_dicts,
        service_dicts,
    ) = _extract_user_context(db, current_user.user_id, today)

    # Investment capacity
    cap_res = compute_investment_capacity(
        snapshot=snapshot,
        goals=goal_inputs,
        liabilities=liab_inputs,
        holdings=hold_inputs,
        today=today,
    )

    # Timeline events for upcoming obligations
    timeline_events = build_timeline_events(
        reminders=[],
        liabilities=liab_dicts,
        services=service_dicts,
        appliances=appliance_dicts,
        goals=goal_dicts,
        today=today,
    )

    # Top recommendation (from latest stored recommendations, or compute live top)
    top_rec: dict[str, Any] | None = None
    stored_rec = (
        db.query(Recommendation)
        .filter(Recommendation.user_id == current_user.user_id)
        .order_by(Recommendation.created_at.desc(), Recommendation.priority_rank.asc())
        .first()
    )
    if stored_rec:
        top_rec = {
            "recommendation_id": stored_rec.recommendation_id,
            "priority_rank": stored_rec.priority_rank,
            "rec_type": stored_rec.rec_type,
            "action": stored_rec.action,
            "reason": stored_rec.reason,
            "status": stored_rec.status,
            "explanation_text": stored_rec.explanation_text,
            "explanation_source": stored_rec.explanation_source,
        }
    else:
        # Fallback to pure advisor plan top rec
        latest_profile = (
            db.query(RiskProfile)
            .filter(RiskProfile.user_id == current_user.user_id)
            .order_by(RiskProfile.assessed_at.desc())
            .first()
        )
        plan = build_advisor_plan(
            snapshot=snapshot,
            capacity=cap_res,
            goals=goal_inputs,
            liabilities=liab_inputs,
            risk_effective_level=latest_profile.effective_level if latest_profile else "moderate",
        )
        if plan.recommendations:
            r = plan.recommendations[0]
            top_rec = {
                "priority_rank": r.priority_rank,
                "rec_type": r.rec_type,
                "action": r.action,
                "reason": r.reason,
                "status": r.status,
            }

    dash = build_dashboard_summary(
        snapshot=snapshot,
        investment_capacity=cap_res.capacity,
        investment_capacity_status=cap_res.status,
        top_recommendation=top_rec,
        timeline_events=timeline_events,
        appliances=appliance_dicts,
        goals=goal_dicts,
        today=today,
    )

    return DashboardResponse(
        snapshot=FinancialSnapshotResponse(
            is_sufficient=dash.snapshot.is_sufficient,
            missing_items=dash.snapshot.missing_items,
            monthly_income=dash.snapshot.monthly_income,
            essential_expenses=dash.snapshot.essential_expenses,
            discretionary_expenses=dash.snapshot.discretionary_expenses,
            total_expenses=dash.snapshot.total_expenses,
            debt_payments=dash.snapshot.debt_payments,
            net_cash_flow=dash.snapshot.net_cash_flow,
            savings_rate=dash.snapshot.savings_rate,
            dti=dash.snapshot.dti,
            dti_level=dash.snapshot.dti_level,
            net_worth=dash.snapshot.net_worth,
            emergency_coverage_months=dash.snapshot.emergency_coverage_months,
            is_stale=dash.snapshot.is_stale,
            stale_reasons=dash.snapshot.stale_reasons,
        ),
        investment_capacity=dash.investment_capacity,
        investment_capacity_status=dash.investment_capacity_status,
        top_recommendation=dash.top_recommendation,
        upcoming_obligations=[
            DashboardObligationSchema(
                id=o.id,
                title=o.title,
                due_date=o.due_date,
                amount=o.amount,
                category=o.category,
                status=o.status,
                details=o.details,
            )
            for o in dash.upcoming_obligations
        ],
        asset_alerts=[
            DashboardAssetAlertSchema(
                appliance_id=a.appliance_id,
                product_name=a.product_name,
                brand=a.brand,
                alert_type=a.alert_type,
                due_date=a.due_date,
                days_remaining=a.days_remaining,
                message=a.message,
            )
            for a in dash.asset_alerts
        ],
        goals_progress=[
            DashboardGoalSummarySchema(
                goal_id=g.goal_id,
                title=g.title,
                target_amount=g.target_amount,
                saved_amount=g.saved_amount,
                progress_percent=g.progress_percent,
                target_date=g.target_date,
                months_left=g.months_left,
                planning_contribution=g.planning_contribution,
            )
            for g in dash.goals_progress
        ],
        physical_assets_estimate=dash.physical_assets_estimate,
        freshness=dash.freshness,
    )


@router.get("/timeline", response_model=TimelineResponse)
def get_timeline(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TimelineResponse:
    """FR-12: Unified chronological calendar and timeline of upcoming events."""
    today = date.today()
    (
        _,
        _,
        _,
        _,
        liab_dicts,
        goal_dicts,
        appliance_dicts,
        service_dicts,
    ) = _extract_user_context(db, current_user.user_id, today)

    events = build_timeline_events(
        reminders=[],
        liabilities=liab_dicts,
        services=service_dicts,
        appliances=appliance_dicts,
        goals=goal_dicts,
        today=today,
    )

    return TimelineResponse(
        events=[
            TimelineEventSchema(
                event_id=e.event_id,
                title=e.title,
                event_date=e.event_date,
                event_type=e.event_type,
                amount=e.amount,
                urgency=e.urgency,
                description=e.description,
                meta=e.meta,
            )
            for e in events
        ],
        today=today,
    )


@router.post("/demo/seed", response_model=DemoSeedResponse, status_code=status.HTTP_200_OK)
def trigger_demo_seed(
    data: DemoSeedRequest,
    db: Session = Depends(get_db),
) -> DemoSeedResponse:
    """Part 7.4 & 6.6: Seed golden demo user (Scenario A or B)."""
    user = seed_demo_user(db, scenario=data.scenario.upper())
    return DemoSeedResponse(
        message=f"Demo user seeded successfully with Scenario {data.scenario.upper()}.",
        scenario=data.scenario.upper(),
        user_email=user.email,
        user_id=user.user_id,
    )
