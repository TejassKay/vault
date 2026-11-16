"""Repository queries for analytics — always filters by user_id."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.holding import Holding
from app.models.income_source import IncomeSource
from app.models.liability import Liability
from app.models.transaction import Transaction


def get_user_transactions(db: Session, user_id: int) -> list[Transaction]:
    return (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id)
        .order_by(Transaction.txn_date.asc(), Transaction.transaction_id.asc())
        .all()
    )


def get_user_income_sources(db: Session, user_id: int) -> list[IncomeSource]:
    return db.query(IncomeSource).filter(IncomeSource.user_id == user_id).all()


def get_user_liabilities(db: Session, user_id: int) -> list[Liability]:
    return db.query(Liability).filter(Liability.user_id == user_id).all()


def get_user_holdings(db: Session, user_id: int) -> list[Holding]:
    return db.query(Holding).filter(Holding.user_id == user_id).all()
