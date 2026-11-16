from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import GoogleAuthRequest, TokenResponse, UserLogin, UserResponse, UserSignup

router = APIRouter(tags=["auth"])


@router.post("/auth/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(data: UserSignup, db: Session = Depends(get_db)) -> UserResponse:
    """FR-1: Register a new user with email, password, and mandatory data processing consent."""
    if not data.consent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consent to data processing is required to create an account.",
        )

    # Normalize email
    normalized_email = data.email.lower().strip()

    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered.",
        )

    hashed_pw = hash_password(data.password)
    new_user = User(
        name=data.name.strip(),
        email=normalized_email,
        password_hash=hashed_pw,
        consent_given_at=datetime.now(UTC),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/auth/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    """FR-1 & NFR-3: Authenticate user credentials and return a signed JWT access token.

    Supports login via email OR username (case-insensitive name match).
    """
    identifier = (data.username or data.email or "").strip().lower()
    if not identifier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email is required.",
        )

    # Try matching email first, then name/username
    user = (
        db.query(User)
        .filter((User.email.ilike(identifier)) | (User.name.ilike(identifier)))
        .first()
    )

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=user.user_id)
    expires_in_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in_seconds,
    )


@router.post("/auth/google", response_model=TokenResponse)
def google_auth(data: GoogleAuthRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Authenticate or register user via Google OAuth."""
    email = (data.email or "google.user@vault.local").strip().lower()
    name = (data.name or "Google User").strip()

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            name=name,
            email=email,
            password_hash=hash_password(f"google_oauth_{email}"),
            consent_given_at=datetime.now(UTC),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = create_access_token(subject=user.user_id)
    expires_in_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in_seconds,
    )


@router.get("/me", response_model=UserResponse)
@router.get("/auth/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """NFR-3: Get current authenticated user profile."""
    return current_user


@router.get("/me/export")
def export_user_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """FR-30: Export all user-owned records as structured JSON."""
    from app.models.appliance import Appliance, Service
    from app.models.bill import Bill
    from app.models.goal import Goal
    from app.models.holding import Holding
    from app.models.income_source import IncomeSource
    from app.models.liability import Liability
    from app.models.recommendation import Recommendation
    from app.models.reminder import Reminder
    from app.models.risk_profile import RiskProfile
    from app.models.transaction import Transaction

    uid = current_user.user_id

    bills = db.query(Bill).filter(Bill.user_id == uid).all()
    appliances = db.query(Appliance).filter(Appliance.user_id == uid).all()
    app_ids = [a.appliance_id for a in appliances]
    services = db.query(Service).filter(Service.appliance_id.in_(app_ids)).all() if app_ids else []
    transactions = db.query(Transaction).filter(Transaction.user_id == uid).all()
    income_sources = db.query(IncomeSource).filter(IncomeSource.user_id == uid).all()
    liabilities = db.query(Liability).filter(Liability.user_id == uid).all()
    holdings = db.query(Holding).filter(Holding.user_id == uid).all()
    goals = db.query(Goal).filter(Goal.user_id == uid).all()
    risk_profiles = db.query(RiskProfile).filter(RiskProfile.user_id == uid).all()
    recommendations = db.query(Recommendation).filter(Recommendation.user_id == uid).all()
    reminders = db.query(Reminder).filter(Reminder.user_id == uid).all()

    return {
        "user": {
            "user_id": current_user.user_id,
            "name": current_user.name,
            "email": current_user.email,
            "consent_given_at": current_user.consent_given_at.isoformat()
            if current_user.consent_given_at
            else None,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        },
        "bills": [
            {
                "bill_id": b.bill_id,
                "file_url": b.file_url,
                "file_type": b.file_type,
                "parse_status": b.parse_status,
                "raw_text": b.raw_text,
                "extraction_json": b.extraction_json,
                "corrected_fields": b.corrected_fields,
                "uploaded_at": b.uploaded_at.isoformat() if b.uploaded_at else None,
            }
            for b in bills
        ],
        "appliances": [
            {
                "appliance_id": a.appliance_id,
                "category_id": a.category_id,
                "product_name": a.product_name,
                "brand": a.brand,
                "model_number": a.model_number,
                "seller": a.seller,
                "price": str(a.price) if a.price else None,
                "purchase_date": a.purchase_date.isoformat() if a.purchase_date else None,
                "warranty_months": a.warranty_months,
                "warranty_end_date": a.warranty_end_date.isoformat()
                if a.warranty_end_date
                else None,
                "estimated_value": str(a.estimated_value) if a.estimated_value else None,
            }
            for a in appliances
        ],
        "services": [
            {
                "service_id": s.service_id,
                "appliance_id": s.appliance_id,
                "due_date": s.due_date.isoformat() if s.due_date else None,
                "status": s.status,
                "cost": str(s.cost) if s.cost else None,
                "guidance_label": s.guidance_label,
                "note": s.note,
            }
            for s in services
        ],
        "transactions": [
            {
                "transaction_id": t.transaction_id,
                "type": t.type,
                "amount": str(t.amount),
                "category": t.category,
                "txn_date": t.txn_date.isoformat(),
                "note": t.note,
                "is_recurring": t.is_recurring,
            }
            for t in transactions
        ],
        "income_sources": [
            {
                "income_source_id": i.income_source_id,
                "name": i.name,
                "amount": str(i.amount),
                "frequency": i.frequency,
                "income_type": i.income_type,
                "expected_day": i.expected_day,
                "is_active": i.is_active,
            }
            for i in income_sources
        ],
        "liabilities": [
            {
                "liability_id": liab.liability_id,
                "type": liab.type,
                "lender_name": liab.lender_name,
                "outstanding_principal": str(liab.outstanding_principal),
                "interest_rate": str(liab.interest_rate),
                "emi_amount": str(liab.emi_amount),
                "due_day": liab.due_day,
                "remaining_months": liab.remaining_months,
                "status": liab.status,
            }
            for liab in liabilities
        ],
        "holdings": [
            {
                "holding_id": h.holding_id,
                "type": h.type,
                "name": h.name,
                "current_value": str(h.current_value),
                "as_of_date": h.as_of_date.isoformat(),
                "liquidity": h.liquidity,
                "is_emergency_reserve": h.is_emergency_reserve,
                "source": h.source,
            }
            for h in holdings
        ],
        "goals": [
            {
                "goal_id": g.goal_id,
                "title": g.title,
                "target_amount": str(g.target_amount),
                "saved_amount": str(g.saved_amount),
                "target_date": g.target_date.isoformat(),
                "priority": g.priority,
                "liquidity_need": g.liquidity_need,
                "status": g.status,
            }
            for g in goals
        ],
        "risk_profiles": [
            {
                "risk_profile_id": rp.risk_profile_id,
                "answers": rp.answers,
                "score": rp.score,
                "tolerance_level": rp.tolerance_level,
                "capacity_level": rp.capacity_level,
                "effective_level": rp.effective_level,
                "assessed_at": rp.assessed_at.isoformat(),
            }
            for rp in risk_profiles
        ],
        "recommendations": [
            {
                "recommendation_id": r.recommendation_id,
                "priority_rank": r.priority_rank,
                "rec_type": r.rec_type,
                "action": r.action,
                "reason": r.reason,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
            }
            for r in recommendations
        ],
        "reminders": [
            {
                "reminder_id": rem.reminder_id,
                "type": rem.type,
                "remind_on": rem.remind_on.isoformat(),
                "message": rem.message,
                "sent": rem.sent,
            }
            for rem in reminders
        ],
    }


def clear_user_ledger_data(db: Session, user_id: int) -> None:
    """Delete all ledger records for `user_id` while keeping the User account intact."""
    from app.models.appliance import Appliance, Service
    from app.models.bill import Bill
    from app.models.goal import Goal
    from app.models.holding import Holding
    from app.models.income_source import IncomeSource
    from app.models.liability import Liability
    from app.models.recommendation import Recommendation
    from app.models.reminder import Reminder
    from app.models.risk_profile import RiskProfile
    from app.models.transaction import Transaction

    db.query(Reminder).filter(Reminder.user_id == user_id).delete(synchronize_session=False)
    appliance_ids = [
        a.appliance_id
        for a in db.query(Appliance.appliance_id).filter(Appliance.user_id == user_id).all()
    ]
    if appliance_ids:
        db.query(Service).filter(Service.appliance_id.in_(appliance_ids)).delete(
            synchronize_session=False
        )
    db.query(Appliance).filter(Appliance.user_id == user_id).delete(synchronize_session=False)
    db.query(Bill).filter(Bill.user_id == user_id).delete(synchronize_session=False)
    db.query(Transaction).filter(Transaction.user_id == user_id).delete(synchronize_session=False)
    db.query(IncomeSource).filter(IncomeSource.user_id == user_id).delete(synchronize_session=False)
    db.query(Liability).filter(Liability.user_id == user_id).delete(synchronize_session=False)
    db.query(Holding).filter(Holding.user_id == user_id).delete(synchronize_session=False)
    db.query(Goal).filter(Goal.user_id == user_id).delete(synchronize_session=False)
    db.query(RiskProfile).filter(RiskProfile.user_id == user_id).delete(synchronize_session=False)
    db.query(Recommendation).filter(Recommendation.user_id == user_id).delete(
        synchronize_session=False
    )


@router.post("/me/reset", status_code=status.HTTP_204_NO_CONTENT)
def reset_user_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Clear all financial, asset, and advisory records for the current user without deleting the account."""
    clear_user_ledger_data(db, current_user.user_id)
    db.commit()


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """FR-30: Permanently delete current user account and all cascaded data."""
    db.delete(current_user)
    db.commit()
