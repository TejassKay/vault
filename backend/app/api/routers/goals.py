"""FR-9, FR-27: Goals Router."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.engines.goal_engine import compute_goal_projection
from app.models.goal import Goal
from app.models.user import User
from app.schemas.finance import (
    GoalAddSavingRequest,
    GoalCreate,
    GoalProjectionResponse,
    GoalResponse,
)
from app.services.reminder_service import create_goal_reminders

router = APIRouter(prefix="/goals", tags=["goals"])


@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(
    data: GoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GoalResponse:
    goal = Goal(
        user_id=current_user.user_id,
        title=data.title,
        target_amount=data.target_amount,
        saved_amount=data.saved_amount,
        target_date=data.target_date,
        priority=data.priority,
        liquidity_need=data.liquidity_need,
        status=data.status,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)

    # FR-6: Create goal deadline reminder
    create_goal_reminders(goal, db, date.today())
    db.commit()

    return GoalResponse.model_validate(goal)


@router.get("", response_model=list[GoalResponse])
def list_goals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[GoalResponse]:
    goals = db.query(Goal).filter(Goal.user_id == current_user.user_id).all()
    return [GoalResponse.model_validate(g) for g in goals]


@router.get("/{goal_id}", response_model=GoalResponse)
def get_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GoalResponse:
    goal = (
        db.query(Goal)
        .filter(
            Goal.goal_id == goal_id,
            Goal.user_id == current_user.user_id,
        )
        .first()
    )
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found.")
    return GoalResponse.model_validate(goal)


@router.post("/{goal_id}/add-saving", response_model=GoalResponse)
def add_saving(
    goal_id: int,
    data: GoalAddSavingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GoalResponse:
    goal = (
        db.query(Goal)
        .filter(
            Goal.goal_id == goal_id,
            Goal.user_id == current_user.user_id,
        )
        .first()
    )
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found.")

    goal.saved_amount += data.amount
    if goal.saved_amount >= goal.target_amount:
        goal.status = "achieved"

    db.commit()
    db.refresh(goal)
    return GoalResponse.model_validate(goal)


@router.get("/{goal_id}/projection", response_model=GoalProjectionResponse)
def get_goal_projection(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GoalProjectionResponse:
    goal = (
        db.query(Goal)
        .filter(
            Goal.goal_id == goal_id,
            Goal.user_id == current_user.user_id,
        )
        .first()
    )
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found.")

    today = date.today()
    proj = compute_goal_projection(
        goal_id=goal.goal_id,
        title=goal.title,
        target_amount=goal.target_amount,
        saved_amount=goal.saved_amount,
        target_date=goal.target_date,
        today=today,
    )

    scenarios_list = [
        {
            "rate_percent": float(s.rate_percent),
            "required_contribution": float(s.required_monthly_contribution),
        }
        for s in proj.scenarios
    ]

    return GoalProjectionResponse(
        goal_id=proj.goal_id,
        title=proj.title,
        target_amount=proj.target_amount,
        saved_amount=proj.saved_amount,
        target_date=proj.target_date,
        months_left=proj.months_left,
        progress_percent=proj.progress_percent,
        planning_contribution=proj.planning_contribution,
        scenarios=scenarios_list,
        disclaimer=proj.disclaimer,
    )
