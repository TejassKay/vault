"""FR-2, NFR-3: Bill repository — always filters by user_id."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.bill import Bill


def get_bill(db: Session, bill_id: int, user_id: int) -> Bill | None:
    """Return bill owned by user_id or None."""
    return db.query(Bill).filter(Bill.bill_id == bill_id, Bill.user_id == user_id).first()


def get_bills(db: Session, user_id: int) -> list[Bill]:
    """Return all bills for the user ordered by upload time."""
    return db.query(Bill).filter(Bill.user_id == user_id).order_by(Bill.uploaded_at.desc()).all()


def create_bill(db: Session, **kwargs: object) -> Bill:
    bill = Bill(**kwargs)
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return bill


def update_bill(db: Session, bill: Bill, **kwargs: object) -> Bill:
    for key, value in kwargs.items():
        setattr(bill, key, value)
    db.commit()
    db.refresh(bill)
    return bill
