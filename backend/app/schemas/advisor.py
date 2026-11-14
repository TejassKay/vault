"""Pydantic schemas for Risk Questionnaire, Investment Capacity, and Recommendations."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class QuestionOptionSchema(BaseModel):
    text: str
    score: int


class RiskQuestionSchema(BaseModel):
    id: str
    text: str
    options: list[QuestionOptionSchema]


class RiskQuestionnaireResponse(BaseModel):
    questions: list[RiskQuestionSchema]


class RiskProfileCreate(BaseModel):
    answers: dict[str, Any] = Field(..., description="Mapping of question id or q1..q8 to score (1-4)")


class RiskProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    risk_profile_id: int
    user_id: int
    answers: dict[str, Any]
    score: int
    tolerance_level: str
    capacity_level: str
    effective_level: str
    assessed_at: datetime


class CapacityStepSchema(BaseModel):
    step_number: int
    name: str
    value: Decimal | None
    description: str


class InvestmentCapacityResponse(BaseModel):
    status: str  # ok, blocked, insufficient_data
    capacity: Decimal | None
    capacity_if_clear: Decimal | None
    surplus: Decimal | None
    goal_contribution: Decimal | None
    emergency_top_up: Decimal | None
    remaining: Decimal | None
    steps: list[CapacityStepSchema]
    reason_codes: list[str]
    missing_items: list[str]
    assumptions: list[str]


class RecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    recommendation_id: int
    user_id: int
    priority_rank: int
    rec_type: str
    action: str
    reason: str
    assumptions: list[str] | dict[str, Any] | None = None
    risks: list[str] | dict[str, Any] | None = None
    alternatives: list[str] | dict[str, Any] | None = None
    review_trigger: str | None = None
    inputs_snapshot: dict[str, Any]
    engine_version: str
    explanation_text: str | None = None
    explanation_source: str | None = None  # llm, template
    status: str  # proposed, accepted, edited, rejected
    created_at: datetime
    decided_at: datetime | None = None


class RecommendationUpdate(BaseModel):
    status: Literal["proposed", "accepted", "edited", "rejected"]


class RecommendationListResponse(BaseModel):
    recommendations: list[RecommendationResponse]
    disclaimer: str
