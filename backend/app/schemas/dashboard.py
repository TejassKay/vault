"""Pydantic schemas for Dashboard, Timeline, and Demo Seed."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel

from app.schemas.finance import FinancialSnapshotResponse


class DashboardObligationSchema(BaseModel):
    id: str
    title: str
    due_date: date
    amount: Decimal | None = None
    category: str
    status: str
    details: str | None = None


class DashboardAssetAlertSchema(BaseModel):
    appliance_id: int
    product_name: str
    brand: str | None = None
    alert_type: str
    due_date: date
    days_remaining: int
    message: str


class DashboardGoalSummarySchema(BaseModel):
    goal_id: int
    title: str
    target_amount: Decimal
    saved_amount: Decimal
    progress_percent: Decimal
    target_date: date
    months_left: int
    planning_contribution: Decimal


class DashboardResponse(BaseModel):
    snapshot: FinancialSnapshotResponse
    investment_capacity: Decimal | None = None
    investment_capacity_status: str
    top_recommendation: dict[str, Any] | None = None
    upcoming_obligations: list[DashboardObligationSchema]
    asset_alerts: list[DashboardAssetAlertSchema]
    goals_progress: list[DashboardGoalSummarySchema]
    physical_assets_estimate: Decimal
    freshness: dict[str, Any]


class TimelineEventSchema(BaseModel):
    event_id: str
    title: str
    event_date: date
    event_type: str
    amount: Decimal | None = None
    urgency: str
    description: str
    meta: dict[str, Any]


class TimelineResponse(BaseModel):
    events: list[TimelineEventSchema]
    today: date


class DemoSeedRequest(BaseModel):
    scenario: Literal["A", "B", "a", "b"] = "A"


class DemoSeedResponse(BaseModel):
    message: str
    scenario: str
    user_email: str
    user_id: int
