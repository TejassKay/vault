"""FR-7, FR-8, FR-10, FR-15 to FR-20: Financial Records & Snapshot Router."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.engines.budget_engine import compute_budget_nudge
from app.engines.financial_engine import (
    ExpenseInput,
    HoldingInput,
    IncomeInput,
    LiabilityInput,
    compute_financial_snapshot,
)
from app.models.holding import Holding
from app.models.income_source import IncomeSource
from app.models.liability import Liability
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.finance import (
    FinancialSnapshotResponse,
    HoldingCreate,
    HoldingResponse,
    IncomeSourceCreate,
    IncomeSourceResponse,
    LiabilityCreate,
    LiabilityResponse,
    TransactionCreate,
    TransactionPostResponse,
    TransactionResponse,
)
from app.services.reminder_service import create_liability_reminders

router = APIRouter(tags=["finance"])


# ---------------------------------------------------------------------------
# Transactions (FR-7, FR-8)
# ---------------------------------------------------------------------------


@router.post(
    "/transactions", response_model=TransactionPostResponse, status_code=status.HTTP_201_CREATED
)
def create_transaction(
    data: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TransactionPostResponse:
    txn = Transaction(
        user_id=current_user.user_id,
        type=data.type,
        amount=data.amount,
        category=data.category,
        txn_date=data.txn_date,
        note=data.note,
        is_recurring=data.is_recurring,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)

    # FR-8: Compute Budgeting Nudge
    today = date.today()
    # Current month txns
    curr_txns = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == current_user.user_id,
            Transaction.type == "expense",
            Transaction.txn_date >= today.replace(day=1),
            Transaction.txn_date <= today,
        )
        .all()
    )
    # Previous month txns
    first_of_this_month = today.replace(day=1)
    if first_of_this_month.month == 1:
        prev_month_start = date(first_of_this_month.year - 1, 12, 1)
        prev_month_end = date(first_of_this_month.year - 1, 12, 31)
    else:
        prev_month_start = date(first_of_this_month.year, first_of_this_month.month - 1, 1)
        # last day of prev month is 1 day before first_of_this_month
        import datetime

        prev_month_end = first_of_this_month - datetime.timedelta(days=1)

    prev_txns = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == current_user.user_id,
            Transaction.type == "expense",
            Transaction.txn_date >= prev_month_start,
            Transaction.txn_date <= prev_month_end,
        )
        .all()
    )

    nudge_res = compute_budget_nudge(
        current_month_expenses=[(t.amount, t.category) for t in curr_txns],
        previous_month_expenses=[(t.amount, t.category) for t in prev_txns],
        today=today,
    )

    nudge_dict = None
    if nudge_res.should_show:
        nudge_dict = {
            "message": nudge_res.message,
            "projected": float(nudge_res.projected_amount) if nudge_res.projected_amount else None,
            "previous": float(nudge_res.previous_month_amount)
            if nudge_res.previous_month_amount
            else None,
            "largest_category": nudge_res.largest_category_increase,
        }

    return TransactionPostResponse(
        transaction=TransactionResponse.model_validate(txn),
        nudge=nudge_dict,
    )


@router.get("/transactions", response_model=list[TransactionResponse])
def list_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TransactionResponse]:
    txns = (
        db.query(Transaction)
        .filter(Transaction.user_id == current_user.user_id)
        .order_by(Transaction.txn_date.desc())
        .all()
    )
    return [TransactionResponse.model_validate(t) for t in txns]


@router.delete("/transactions/{txn_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    txn_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    txn = (
        db.query(Transaction)
        .filter(
            Transaction.transaction_id == txn_id,
            Transaction.user_id == current_user.user_id,
        )
        .first()
    )
    if not txn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found.")
    db.delete(txn)
    db.commit()


# ---------------------------------------------------------------------------
# Income Sources (FR-15)
# ---------------------------------------------------------------------------


@router.post(
    "/income-sources", response_model=IncomeSourceResponse, status_code=status.HTTP_201_CREATED
)
def create_income_source(
    data: IncomeSourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IncomeSourceResponse:
    source = IncomeSource(
        user_id=current_user.user_id,
        name=data.name,
        amount=data.amount,
        frequency=data.frequency,
        income_type=data.income_type,
        expected_day=data.expected_day,
        is_active=data.is_active,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return IncomeSourceResponse.model_validate(source)


@router.get("/income-sources", response_model=list[IncomeSourceResponse])
def list_income_sources(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[IncomeSourceResponse]:
    sources = db.query(IncomeSource).filter(IncomeSource.user_id == current_user.user_id).all()
    return [IncomeSourceResponse.model_validate(s) for s in sources]


@router.delete("/income-sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_income_source(
    source_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    source = (
        db.query(IncomeSource)
        .filter(
            IncomeSource.income_source_id == source_id,
            IncomeSource.user_id == current_user.user_id,
        )
        .first()
    )
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Income source not found."
        )
    db.delete(source)
    db.commit()


# ---------------------------------------------------------------------------
# Liabilities (FR-16)
# ---------------------------------------------------------------------------


@router.post("/liabilities", response_model=LiabilityResponse, status_code=status.HTTP_201_CREATED)
def create_liability(
    data: LiabilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LiabilityResponse:
    liability = Liability(
        user_id=current_user.user_id,
        type=data.type,
        lender_name=data.lender_name,
        outstanding_principal=data.outstanding_principal,
        interest_rate=data.interest_rate,
        emi_amount=data.emi_amount,
        due_day=data.due_day,
        remaining_months=data.remaining_months,
        prepayment_note=data.prepayment_note,
        status=data.status,
    )
    db.add(liability)
    db.commit()
    db.refresh(liability)

    # FR-6: Create EMI reminder
    create_liability_reminders(liability, db, date.today())
    db.commit()

    return LiabilityResponse.model_validate(liability)


@router.get("/liabilities", response_model=list[LiabilityResponse])
def list_liabilities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[LiabilityResponse]:
    liabs = db.query(Liability).filter(Liability.user_id == current_user.user_id).all()
    return [LiabilityResponse.model_validate(item) for item in liabs]


@router.delete("/liabilities/{liability_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_liability(
    liability_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    liab = (
        db.query(Liability)
        .filter(
            Liability.liability_id == liability_id,
            Liability.user_id == current_user.user_id,
        )
        .first()
    )
    if not liab:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Liability not found.")
    db.delete(liab)
    db.commit()


# ---------------------------------------------------------------------------
# Holdings (FR-17)
# ---------------------------------------------------------------------------


@router.post("/holdings", response_model=HoldingResponse, status_code=status.HTTP_201_CREATED)
def create_holding(
    data: HoldingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HoldingResponse:
    holding = Holding(
        user_id=current_user.user_id,
        type=data.type,
        name=data.name,
        current_value=data.current_value,
        as_of_date=data.as_of_date,
        liquidity=data.liquidity,
        is_emergency_reserve=data.is_emergency_reserve,
        source=data.source,
    )
    db.add(holding)
    db.commit()
    db.refresh(holding)
    return HoldingResponse.model_validate(holding)


@router.get("/holdings", response_model=list[HoldingResponse])
def list_holdings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[HoldingResponse]:
    holdings = db.query(Holding).filter(Holding.user_id == current_user.user_id).all()
    return [HoldingResponse.model_validate(h) for h in holdings]


@router.delete("/holdings/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_holding(
    holding_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    holding = (
        db.query(Holding)
        .filter(
            Holding.holding_id == holding_id,
            Holding.user_id == current_user.user_id,
        )
        .first()
    )
    if not holding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holding not found.")
    db.delete(holding)
    db.commit()


# ---------------------------------------------------------------------------
# Financial Snapshot (FR-10, FR-18 - FR-20, FR-28, FR-29)
# ---------------------------------------------------------------------------


@router.get("/snapshot", response_model=FinancialSnapshotResponse)
def get_snapshot(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FinancialSnapshotResponse:
    today = date.today()

    sources = db.query(IncomeSource).filter(IncomeSource.user_id == current_user.user_id).all()
    inc_inputs = [
        IncomeInput(
            amount=s.amount,
            frequency=s.frequency,
            is_active=s.is_active,
            updated_at=s.updated_at.date() if s.updated_at else today,
        )
        for s in sources
    ]

    txns = db.query(Transaction).filter(Transaction.user_id == current_user.user_id).all()
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

    liabs = db.query(Liability).filter(Liability.user_id == current_user.user_id).all()
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

    holdings = db.query(Holding).filter(Holding.user_id == current_user.user_id).all()
    hold_inputs = [
        HoldingInput(
            current_value=h.current_value,
            is_emergency_reserve=h.is_emergency_reserve,
            as_of_date=h.as_of_date,
        )
        for h in holdings
    ]

    snap = compute_financial_snapshot(
        income_sources=inc_inputs,
        income_txns=inc_txn_inputs,
        expense_txns=exp_inputs,
        liabilities=liab_inputs,
        holdings=hold_inputs,
        today=today,
    )

    return FinancialSnapshotResponse(
        is_sufficient=snap.is_sufficient,
        missing_items=snap.missing_items,
        monthly_income=snap.monthly_income,
        essential_expenses=snap.essential_expenses,
        discretionary_expenses=snap.discretionary_expenses,
        total_expenses=snap.total_expenses,
        debt_payments=snap.debt_payments,
        net_cash_flow=snap.net_cash_flow,
        savings_rate=snap.savings_rate,
        dti=snap.dti,
        dti_level=snap.dti_level,
        net_worth=snap.net_worth,
        emergency_coverage_months=snap.emergency_coverage_months,
        is_stale=snap.is_stale,
        stale_reasons=snap.stale_reasons,
    )
