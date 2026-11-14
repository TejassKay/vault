"""FR-6.6, Part 5: Seed demo data matching Golden Scenarios A & B."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models.appliance import Appliance, ApplianceCategory
from app.models.goal import Goal
from app.models.holding import Holding
from app.models.income_source import IncomeSource
from app.models.liability import Liability
from app.models.transaction import Transaction
from app.models.user import User
from app.seed.seed_intervals import seed_service_intervals

DEMO_USER_EMAIL = "demo@vault.local"


def seed_demo_user(db: Session, scenario: str = "A") -> User:
    """Seed or update demo user according to Part 6.6 golden dataset.

    Today = 2026-11-13 (or current date baseline)
    Salary: 85,000 monthly, fixed
    Expenses across Aug, Sep, Oct 2026:
      Essential: Rent 18,000, Groceries 8,000, Utilities 3,000, Transport 3,000 (Total: 32,000)
      Discretionary: Food-out 4,000, Entertainment 4,000 (Total: 8,000)
    Liability: personal loan, outstanding 2,40,000, rate 11.00%, EMI 10,000, due day 5, 30 months remaining
    Holdings:
      Scenario A: savings account 45,000 (emergency reserve) + mutual fund 2,50,000 (not reserve)
      Scenario B: savings account 2,60,000 (emergency reserve) + mutual fund 2,50,000 (not reserve)
    Goal: Car down payment, target 5,00,000, saved 50,000, target date 2028-11-13, priority high
    Appliance: Daikin AC, 45,000, purchase 2025-11-13, warranty 12 mo (ends 2026-11-13)
    """
    user = db.query(User).filter(User.email == DEMO_USER_EMAIL).first()
    if not user:
        user = User(
            name="Demo User",
            email=DEMO_USER_EMAIL,
            password_hash=hash_password("DemoPassword123!"),
            consent_given_at=datetime.now(UTC),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    uid = user.user_id

    # Clean existing data for a fresh scenario state
    db.query(Transaction).filter(Transaction.user_id == uid).delete()
    db.query(IncomeSource).filter(IncomeSource.user_id == uid).delete()
    db.query(Liability).filter(Liability.user_id == uid).delete()
    db.query(Holding).filter(Holding.user_id == uid).delete()
    db.query(Goal).filter(Goal.user_id == uid).delete()
    db.commit()

    # 1. Income Source: Salary ₹85,000
    db.add(
        IncomeSource(
            user_id=uid,
            name="Corporate Salary",
            amount=Decimal("85000.00"),
            frequency="monthly",
            income_type="fixed",
            expected_day=1,
            is_active=True,
        )
    )

    # 2. Expenses across Aug, Sep, Oct 2026
    for m in [8, 9, 10]:
        db.add(
            Transaction(
                user_id=uid,
                type="expense",
                amount=Decimal("18000.00"),
                category="Rent",
                txn_date=date(2026, m, 5),
            )
        )
        db.add(
            Transaction(
                user_id=uid,
                type="expense",
                amount=Decimal("8000.00"),
                category="Groceries",
                txn_date=date(2026, m, 10),
            )
        )
        db.add(
            Transaction(
                user_id=uid,
                type="expense",
                amount=Decimal("3000.00"),
                category="Utilities",
                txn_date=date(2026, m, 15),
            )
        )
        db.add(
            Transaction(
                user_id=uid,
                type="expense",
                amount=Decimal("3000.00"),
                category="Transport",
                txn_date=date(2026, m, 20),
            )
        )
        db.add(
            Transaction(
                user_id=uid,
                type="expense",
                amount=Decimal("4000.00"),
                category="Food-out",
                txn_date=date(2026, m, 22),
            )
        )
        db.add(
            Transaction(
                user_id=uid,
                type="expense",
                amount=Decimal("4000.00"),
                category="Entertainment",
                txn_date=date(2026, m, 25),
            )
        )

    # 3. Liability: Personal Loan ₹2,40,000 @ 11.00%, EMI ₹10,000
    db.add(
        Liability(
            user_id=uid,
            type="personal",
            lender_name="HDFC Bank",
            outstanding_principal=Decimal("240000.00"),
            interest_rate=Decimal("11.00"),
            emi_amount=Decimal("10000.00"),
            due_day=5,
            remaining_months=30,
            status="active",
        )
    )

    # 4. Holdings: Scenario A (₹45k reserve) vs Scenario B (₹260k reserve)
    reserve_amt = Decimal("45000.00") if scenario.upper() == "A" else Decimal("260000.00")
    db.add(
        Holding(
            user_id=uid,
            type="bank_savings",
            name="Liquid Emergency Fund",
            current_value=reserve_amt,
            as_of_date=date(2026, 11, 1),
            liquidity="liquid",
            is_emergency_reserve=True,
            source="manual",
        )
    )
    db.add(
        Holding(
            user_id=uid,
            type="mutual_fund",
            name="Diversified Equity Index Fund",
            current_value=Decimal("250000.00"),
            as_of_date=date(2026, 11, 1),
            liquidity="semi_liquid",
            is_emergency_reserve=False,
            source="manual",
        )
    )

    # 5. Goal: Car Down Payment
    db.add(
        Goal(
            user_id=uid,
            title="Car down payment",
            target_amount=Decimal("500000.00"),
            saved_amount=Decimal("50000.00"),
            target_date=date(2028, 11, 13),
            priority="high",
            liquidity_need="medium",
            status="active",
        )
    )

    # 6. Appliance if category exists
    cat = db.query(ApplianceCategory).first()
    if not cat:
        seed_service_intervals(db)
        cat = db.query(ApplianceCategory).first()

    if cat:
        existing_app = db.query(Appliance).filter(Appliance.user_id == uid).first()
        if not existing_app:
            db.add(
                Appliance(
                    user_id=uid,
                    category_id=cat.category_id,
                    product_name="Daikin Split Air Conditioner 1.5 Ton",
                    brand="Daikin",
                    model_number="FTKF50TV",
                    seller="Croma Electronics",
                    price=Decimal("45000.00"),
                    purchase_date=date(2025, 11, 13),
                    warranty_months=12,
                    warranty_end_date=date(2026, 11, 13),
                    estimated_value=Decimal("38000.00"),
                )
            )

    db.commit()
    db.refresh(user)
    return user


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Seed demo user data according to Spec 6.6.")
    parser.add_argument(
        "--scenario",
        type=str,
        default="A",
        help="Golden scenario to seed: A or B (default: A)",
    )
    args = parser.parse_args()
    scenario = args.scenario.upper()

    # Ensure tables exist on an empty database
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        seed_service_intervals(session)
        user = seed_demo_user(session, scenario=scenario)
        print(f"Demo user '{user.email}' seeded successfully for Scenario {scenario}.")
