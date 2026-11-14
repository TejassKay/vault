"""FR-7 to FR-9, FR-15 to FR-17: Pydantic schemas for finance core."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Transactions (FR-7)
# ---------------------------------------------------------------------------


class TransactionCreate(BaseModel):
    type: str  # income, expense
    amount: Decimal = Field(..., gt=0)
    category: str
    txn_date: date
    note: str | None = None
    is_recurring: bool = False


class TransactionUpdate(BaseModel):
    type: str | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    category: str | None = None
    txn_date: date | None = None
    note: str | None = None
    is_recurring: bool | None = None


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    transaction_id: int
    user_id: int
    type: str
    amount: Decimal
    category: str
    txn_date: date
    note: str | None = None
    is_recurring: bool


class TransactionPostResponse(BaseModel):
    transaction: TransactionResponse
    nudge: Any | None = None


# ---------------------------------------------------------------------------
# Income Sources (FR-15)
# ---------------------------------------------------------------------------


class IncomeSourceCreate(BaseModel):
    name: str
    amount: Decimal = Field(..., gt=0)
    frequency: str  # monthly, weekly, yearly, one_time
    income_type: str  # fixed, variable
    expected_day: int | None = Field(default=None, ge=1, le=31)
    is_active: bool = True


class IncomeSourceUpdate(BaseModel):
    name: str | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    frequency: str | None = None
    income_type: str | None = None
    expected_day: int | None = Field(default=None, ge=1, le=31)
    is_active: bool | None = None


class IncomeSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    income_source_id: int
    user_id: int
    name: str
    amount: Decimal
    frequency: str
    income_type: str
    expected_day: int | None = None
    is_active: bool
    updated_at: datetime | None = None


# ---------------------------------------------------------------------------
# Liabilities (FR-16)
# ---------------------------------------------------------------------------


class LiabilityCreate(BaseModel):
    type: str  # home, vehicle, education, personal, credit_card, other
    lender_name: str | None = None
    outstanding_principal: Decimal = Field(..., ge=0)
    interest_rate: Decimal = Field(..., ge=0)
    emi_amount: Decimal = Field(..., ge=0)
    due_day: int = Field(..., ge=1, le=31)
    remaining_months: int | None = Field(default=None, ge=0)
    prepayment_note: str | None = None
    status: str = "active"


class LiabilityUpdate(BaseModel):
    type: str | None = None
    lender_name: str | None = None
    outstanding_principal: Decimal | None = Field(default=None, ge=0)
    interest_rate: Decimal | None = Field(default=None, ge=0)
    emi_amount: Decimal | None = Field(default=None, ge=0)
    due_day: int | None = Field(default=None, ge=1, le=31)
    remaining_months: int | None = Field(default=None, ge=0)
    prepayment_note: str | None = None
    status: str | None = None


class LiabilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    liability_id: int
    user_id: int
    type: str
    lender_name: str | None = None
    outstanding_principal: Decimal
    interest_rate: Decimal
    emi_amount: Decimal
    due_day: int
    remaining_months: int | None = None
    prepayment_note: str | None = None
    status: str
    updated_at: datetime | None = None


# ---------------------------------------------------------------------------
# Holdings (FR-17)
# ---------------------------------------------------------------------------


class HoldingCreate(BaseModel):
    type: str  # bank_savings, fixed_deposit, mutual_fund, stocks, bonds, gold, retirement, other
    name: str
    current_value: Decimal = Field(..., ge=0)
    as_of_date: date
    liquidity: str = "liquid"  # liquid, semi_liquid, locked
    is_emergency_reserve: bool = False
    source: str = "manual"


class HoldingUpdate(BaseModel):
    type: str | None = None
    name: str | None = None
    current_value: Decimal | None = Field(default=None, ge=0)
    as_of_date: date | None = None
    liquidity: str | None = None
    is_emergency_reserve: bool | None = None


class HoldingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    holding_id: int
    user_id: int
    type: str
    name: str
    current_value: Decimal
    as_of_date: date
    liquidity: str
    is_emergency_reserve: bool
    source: str


# ---------------------------------------------------------------------------
# Goals (FR-9, FR-27)
# ---------------------------------------------------------------------------


class GoalCreate(BaseModel):
    title: str
    target_amount: Decimal = Field(..., gt=0)
    saved_amount: Decimal = Field(default=Decimal("0"), ge=0)
    target_date: date
    priority: str = "medium"  # high, medium, low
    liquidity_need: str = "medium"
    status: str = "active"


class GoalUpdate(BaseModel):
    title: str | None = None
    target_amount: Decimal | None = Field(default=None, gt=0)
    saved_amount: Decimal | None = Field(default=None, ge=0)
    target_date: date | None = None
    priority: str | None = None
    liquidity_need: str | None = None
    status: str | None = None


class GoalAddSavingRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)


class GoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    goal_id: int
    user_id: int
    title: str
    target_amount: Decimal
    saved_amount: Decimal
    target_date: date
    priority: str
    liquidity_need: str
    status: str
    updated_at: datetime | None = None


class GoalProjectionResponse(BaseModel):
    goal_id: int
    title: str
    target_amount: Decimal
    saved_amount: Decimal
    target_date: date
    months_left: int
    progress_percent: Decimal
    planning_contribution: Decimal
    scenarios: list[dict[str, Any]]
    disclaimer: str


# ---------------------------------------------------------------------------
# Snapshot (FR-10, FR-18 - FR-20, FR-28, FR-29)
# ---------------------------------------------------------------------------


class FinancialSnapshotResponse(BaseModel):
    is_sufficient: bool
    missing_items: list[str] = []
    monthly_income: Decimal
    essential_expenses: Decimal
    discretionary_expenses: Decimal
    total_expenses: Decimal
    debt_payments: Decimal
    net_cash_flow: Decimal
    savings_rate: Decimal
    dti: Decimal
    dti_level: str
    net_worth: Decimal
    emergency_coverage_months: Decimal
    is_stale: bool
    stale_reasons: list[str] = []
