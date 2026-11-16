"""Spending Insights Analytics Router."""

from __future__ import annotations

import re
from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.engines.analytics import (
    AnalyticsHoldingInput,
    AnalyticsLiabilityInput,
    compute_analytics_summary,
)
from app.engines.financial_engine import ExpenseInput, IncomeInput
from app.models.user import User
from app.repositories.analytics_repository import (
    get_user_holdings,
    get_user_income_sources,
    get_user_liabilities,
    get_user_transactions,
)
from app.schemas.analytics import (
    AnalyticsMetaSchema,
    AnalyticsSummaryResponse,
    CategoryBreakdownItemSchema,
    CategoryBreakdownSchema,
    CategoryCompareItemSchema,
    CategoryTrendMonthSchema,
    CategoryTrendSchema,
    CompositionSchema,
    HoldingCompositionItemSchema,
    HoldingsCompositionSchema,
    LiabilitiesCompositionSchema,
    LiabilityCompositionItemSchema,
    MonthlySeriesItemSchema,
    PacePointSchema,
    SpendingPaceSchema,
)

router = APIRouter(tags=["analytics"])

_MONTH_RE = re.compile(r"^(\d{4})-(\d{2})$")


def _parse_month(month_param: str | None, today: date) -> date:
    if month_param is None:
        return today.replace(day=1)
    match = _MONTH_RE.match(month_param.strip())
    if not match:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="month must be in YYYY-MM format",
        )
    year, mon = int(match.group(1)), int(match.group(2))
    if mon < 1 or mon > 12:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="month must be between 01 and 12",
        )
    return date(year, mon, 1)


@router.get("/analytics/summary", response_model=AnalyticsSummaryResponse)
def get_analytics_summary(
    month: str | None = Query(default=None, description="Selected month (YYYY-MM)"),
    months: int = Query(default=6, description="Prior full months window: 3, 6, or 12"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalyticsSummaryResponse:
    if months not in (3, 6, 12):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="months must be 3, 6, or 12",
        )

    today = date.today()
    selected_month_start = _parse_month(month, today)

    txns = get_user_transactions(db, current_user.user_id)
    income_sources = get_user_income_sources(db, current_user.user_id)
    liabilities = get_user_liabilities(db, current_user.user_id)
    holdings = get_user_holdings(db, current_user.user_id)

    inc_inputs = [
        IncomeInput(
            amount=s.amount,
            frequency=s.frequency,
            is_active=s.is_active,
            updated_at=s.updated_at.date() if s.updated_at else today,
        )
        for s in income_sources
    ]
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
    liab_inputs = [
        AnalyticsLiabilityInput(
            type=liab.type,
            outstanding_principal=liab.outstanding_principal,
            emi_amount=liab.emi_amount,
            status=liab.status,
        )
        for liab in liabilities
    ]
    hold_inputs = [
        AnalyticsHoldingInput(type=h.type, current_value=h.current_value) for h in holdings
    ]

    summary = compute_analytics_summary(
        income_sources=inc_inputs,
        income_txns=inc_txn_inputs,
        expense_txns=exp_inputs,
        liabilities=liab_inputs,
        holdings=hold_inputs,
        selected_month_start=selected_month_start,
        months=months,
        today=today,
    )

    return AnalyticsSummaryResponse(
        month=summary.month,
        months=summary.months,
        category_breakdown=CategoryBreakdownSchema(
            items=[
                CategoryBreakdownItemSchema(
                    category=item.category,
                    amount=item.amount,
                    share_percent=item.share_percent,
                )
                for item in summary.category_breakdown.items
            ],
            total=summary.category_breakdown.total,
        ),
        monthly_series=[
            MonthlySeriesItemSchema(
                month=m.month,
                income=m.income,
                expenses=m.expenses,
                essential=m.essential,
                discretionary=m.discretionary,
                net=m.net,
                debt_payments=m.debt_payments,
            )
            for m in summary.monthly_series
        ],
        category_trend=CategoryTrendSchema(
            categories=summary.category_trend.categories,
            series=[
                CategoryTrendMonthSchema(month=pt.month, totals=pt.totals)
                for pt in summary.category_trend.series
            ],
        ),
        spending_pace=SpendingPaceSchema(
            current_month=[
                PacePointSchema(day=p.day, cumulative=p.cumulative)
                for p in summary.spending_pace.current_month
            ],
            previous_month=[
                PacePointSchema(day=p.day, cumulative=p.cumulative)
                for p in summary.spending_pace.previous_month
            ],
            comparison_day=summary.spending_pace.comparison_day,
            delta_at_day=summary.spending_pace.delta_at_day,
        ),
        compare=[
            CategoryCompareItemSchema(
                category=c.category,
                amount=c.amount,
                previous=c.previous,
                delta=c.delta,
                delta_percent=c.delta_percent,
            )
            for c in summary.compare
        ],
        composition=CompositionSchema(
            holdings=HoldingsCompositionSchema(
                items=[
                    HoldingCompositionItemSchema(
                        type=h.type, value=h.value, share_percent=h.share_percent
                    )
                    for h in summary.composition.holdings_items
                ],
                total=summary.composition.holdings_total,
            ),
            liabilities=LiabilitiesCompositionSchema(
                items=[
                    LiabilityCompositionItemSchema(
                        type=liab.type,
                        outstanding_principal=liab.outstanding_principal,
                        share_percent=liab.share_percent,
                    )
                    for liab in summary.composition.liabilities_items
                ],
                total=summary.composition.liabilities_total,
            ),
        ),
        meta=AnalyticsMetaSchema(
            generated_at=datetime.now(UTC),
            months_available=summary.months_available,
            has_data=summary.has_data,
        ),
    )
