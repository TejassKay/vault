"""Pydantic schemas for Spending Insights analytics endpoint."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class CategoryBreakdownItemSchema(BaseModel):
    category: str
    amount: Decimal
    share_percent: Decimal


class CategoryBreakdownSchema(BaseModel):
    items: list[CategoryBreakdownItemSchema]
    total: Decimal


class MonthlySeriesItemSchema(BaseModel):
    month: str
    income: Decimal
    expenses: Decimal
    essential: Decimal
    discretionary: Decimal
    net: Decimal
    debt_payments: Decimal


class CategoryTrendMonthSchema(BaseModel):
    month: str
    totals: dict[str, Decimal]


class CategoryTrendSchema(BaseModel):
    categories: list[str]
    series: list[CategoryTrendMonthSchema]


class PacePointSchema(BaseModel):
    day: int
    cumulative: Decimal


class SpendingPaceSchema(BaseModel):
    current_month: list[PacePointSchema]
    previous_month: list[PacePointSchema]
    comparison_day: int
    delta_at_day: Decimal


class CategoryCompareItemSchema(BaseModel):
    category: str
    amount: Decimal
    previous: Decimal
    delta: Decimal
    delta_percent: Decimal | None = None


class HoldingCompositionItemSchema(BaseModel):
    type: str
    value: Decimal
    share_percent: Decimal


class HoldingsCompositionSchema(BaseModel):
    items: list[HoldingCompositionItemSchema]
    total: Decimal


class LiabilityCompositionItemSchema(BaseModel):
    type: str
    outstanding_principal: Decimal
    share_percent: Decimal


class LiabilitiesCompositionSchema(BaseModel):
    items: list[LiabilityCompositionItemSchema]
    total: Decimal


class CompositionSchema(BaseModel):
    holdings: HoldingsCompositionSchema
    liabilities: LiabilitiesCompositionSchema


class AnalyticsMetaSchema(BaseModel):
    generated_at: datetime
    months_available: int
    has_data: bool


class AnalyticsSummaryResponse(BaseModel):
    month: str
    months: int
    category_breakdown: CategoryBreakdownSchema
    monthly_series: list[MonthlySeriesItemSchema]
    category_trend: CategoryTrendSchema
    spending_pace: SpendingPaceSchema
    compare: list[CategoryCompareItemSchema]
    composition: CompositionSchema
    meta: AnalyticsMetaSchema
