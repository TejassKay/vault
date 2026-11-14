"""Seed Vartika24 and Isha25 demo ledgers relative to today (Task 1)."""

from __future__ import annotations

import argparse
import calendar
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.orm import Session

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.engines.financial_engine import (
    ExpenseInput,
    HoldingInput,
    IncomeInput,
    LiabilityInput,
    compute_financial_snapshot,
)
from app.engines.risk_engine import (
    compute_capacity_level,
    compute_effective_level,
    compute_tolerance_level,
    score_questionnaire,
)
from app.engines.service_scheduler import _add_months, build_schedule, warranty_end_date
from app.models.appliance import Appliance, ApplianceCategory, Service
from app.models.bill import Bill
from app.models.goal import Goal
from app.models.holding import Holding
from app.models.income_source import IncomeSource
from app.models.liability import Liability
from app.models.recommendation import Recommendation
from app.models.reminder import Reminder
from app.models.risk_profile import RiskProfile
from app.models.transaction import Transaction
from app.models.user import User
from app.repositories import appliance_repository
from app.seed.seed_intervals import seed_service_intervals
from app.services.reminder_service import (
    create_appliance_reminders,
    create_goal_reminders,
    create_liability_reminders,
    create_service_reminders,
)


@dataclass(frozen=True)
class SeedSummary:
    name: str
    email: str
    income_sources: int
    transactions: int
    liabilities: int
    holdings: int
    goals: int
    appliances: int
    services: int
    reminders: int


def _q2(val: Decimal) -> Decimal:
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _clear_user_data(db: Session, user: User) -> None:
    """Delete only this user's ledger data, leaving all other users untouched."""
    uid = user.user_id
    db.query(Reminder).filter(Reminder.user_id == uid).delete(synchronize_session=False)
    appliance_ids = [
        a.appliance_id
        for a in db.query(Appliance.appliance_id).filter(Appliance.user_id == uid).all()
    ]
    if appliance_ids:
        db.query(Service).filter(Service.appliance_id.in_(appliance_ids)).delete(
            synchronize_session=False
        )
    db.query(Appliance).filter(Appliance.user_id == uid).delete(synchronize_session=False)
    db.query(Bill).filter(Bill.user_id == uid).delete(synchronize_session=False)
    db.query(Transaction).filter(Transaction.user_id == uid).delete(synchronize_session=False)
    db.query(IncomeSource).filter(IncomeSource.user_id == uid).delete(synchronize_session=False)
    db.query(Liability).filter(Liability.user_id == uid).delete(synchronize_session=False)
    db.query(Holding).filter(Holding.user_id == uid).delete(synchronize_session=False)
    db.query(Goal).filter(Goal.user_id == uid).delete(synchronize_session=False)
    db.query(RiskProfile).filter(RiskProfile.user_id == uid).delete(synchronize_session=False)
    db.query(Recommendation).filter(Recommendation.user_id == uid).delete(synchronize_session=False)
    db.flush()


def _upsert_demo_user(db: Session, *, name: str, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user:
        _clear_user_data(db, user)
        user.name = name
        user.password_hash = hash_password(password)
        if not user.consent_given_at:
            user.consent_given_at = datetime.now(UTC)
        db.flush()
        return user

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        consent_given_at=datetime.now(UTC),
    )
    db.add(user)
    db.flush()
    db.refresh(user)
    return user


def _add_monthly_expenses(
    db: Session,
    user_id: int,
    today: date,
    monthly_items: list[tuple[str, Decimal, int]],
) -> list[Transaction]:
    """Add expense transactions for each of the last 3 full calendar months before today."""
    created: list[Transaction] = []
    first_of_this_month = date(today.year, today.month, 1)
    for offset in (-3, -2, -1):
        month_start = _add_months(first_of_this_month, offset)
        for category, amount, day in monthly_items:
            txn = Transaction(
                user_id=user_id,
                type="expense",
                amount=amount,
                category=category,
                txn_date=date(month_start.year, month_start.month, day),
                is_recurring=False,
            )
            db.add(txn)
            created.append(txn)
    return created


def _add_appliance_with_schedule(
    db: Session,
    *,
    user_id: int,
    categories_by_name: dict[str, ApplianceCategory],
    category_name: str,
    product_name: str,
    brand: str,
    price: Decimal,
    purchase_date: date,
    warranty_months: int,
    today: date,
) -> tuple[Appliance, int, int]:
    category = categories_by_name[category_name]
    w_end = warranty_end_date(purchase_date, warranty_months)
    appliance = appliance_repository.create_appliance(
        db,
        user_id=user_id,
        category_id=category.category_id,
        bill_id=None,
        product_name=product_name,
        brand=brand,
        model_number=None,
        seller="Manual Entry",
        price=price,
        purchase_date=purchase_date,
        warranty_months=warranty_months,
        warranty_end_date=w_end,
    )
    schedule = build_schedule(
        purchase_date=purchase_date,
        warranty_months=warranty_months,
        interval_months=category.interval_months,
        guidance_source=category.guidance_source,
        today=today,
    )
    service_records: list[Service] = []
    for svc_date in schedule:
        svc = Service(
            appliance_id=appliance.appliance_id,
            due_date=svc_date.due_date,
            status="pending",
            guidance_label=svc_date.guidance_label,
        )
        db.add(svc)
        service_records.append(svc)
    db.flush()
    for svc in service_records:
        db.refresh(svc)

    rem_count = len(create_appliance_reminders(appliance, db, today))
    for svc in service_records:
        rem_count += len(create_service_reminders(svc, appliance, db, today))
    return appliance, len(service_records), rem_count


def _save_risk_profile(
    db: Session,
    *,
    user_id: int,
    answers: dict[str, int],
    income_sources: list[IncomeSource],
    txns: list[Transaction],
    liabilities: list[Liability],
    holdings: list[Holding],
    today: date,
) -> RiskProfile:
    snapshot = compute_financial_snapshot(
        income_sources=[
            IncomeInput(
                amount=s.amount,
                frequency=s.frequency,
                is_active=s.is_active,
                updated_at=s.updated_at.date() if s.updated_at else today,
            )
            for s in income_sources
        ],
        income_txns=[],
        expense_txns=[
            ExpenseInput(amount=t.amount, category=t.category, txn_date=t.txn_date)
            for t in txns
            if t.type == "expense"
        ],
        liabilities=[
            LiabilityInput(
                outstanding_principal=li.outstanding_principal,
                interest_rate=li.interest_rate,
                emi_amount=li.emi_amount,
                status=li.status,
                updated_at=li.updated_at.date() if li.updated_at else today,
            )
            for li in liabilities
        ],
        holdings=[
            HoldingInput(
                current_value=h.current_value,
                is_emergency_reserve=h.is_emergency_reserve,
                as_of_date=h.as_of_date,
            )
            for h in holdings
        ],
        today=today,
    )
    score = score_questionnaire(answers)
    tolerance = compute_tolerance_level(score)
    capacity_lvl = compute_capacity_level(
        snapshot.emergency_coverage_months,
        snapshot.dti,
    )
    effective = compute_effective_level(tolerance, capacity_lvl)
    profile = RiskProfile(
        user_id=user_id,
        answers=answers,
        score=score,
        tolerance_level=tolerance,
        capacity_level=capacity_lvl,
        effective_level=effective,
    )
    db.add(profile)
    return profile


def _seed_vartika(
    db: Session, categories_by_name: dict[str, ApplianceCategory], today: date
) -> SeedSummary:
    user = _upsert_demo_user(
        db,
        name="Vartika24",
        email="vartika24@vault.local",
        password="Vartika@24",
    )
    uid = user.user_id

    inc = IncomeSource(
        user_id=uid,
        name="Salary",
        amount=Decimal("120000.00"),
        frequency="monthly",
        income_type="fixed",
        expected_day=1,
        is_active=True,
    )
    db.add(inc)
    income_sources = [inc]

    monthly_expenses: list[tuple[str, Decimal, int]] = [
        ("Rent", Decimal("25000.00"), 2),
        ("Groceries", Decimal("10000.00"), 6),
        ("Utilities", Decimal("4000.00"), 9),
        ("Transport", Decimal("6000.00"), 12),
        ("Health", Decimal("3000.00"), 15),
        ("Food-out", Decimal("8000.00"), 19),
        ("Entertainment", Decimal("5000.00"), 22),
        ("Shopping", Decimal("7000.00"), 26),
    ]
    txns = _add_monthly_expenses(db, uid, today, monthly_expenses)

    # Current month at ~90% of previous month's pace (no nudge)
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    days_elapsed = max(1, today.day)
    prev_total = sum((amt for _, amt, _ in monthly_expenses), Decimal("0"))
    target_mtd = _q2(prev_total * Decimal("0.90") * Decimal(days_elapsed) / Decimal(days_in_month))
    rent_mtd = min(Decimal("25000.00"), target_mtd)
    rem_mtd = _q2(target_mtd - rent_mtd)
    if rent_mtd > Decimal("0"):
        t_rent = Transaction(
            user_id=uid,
            type="expense",
            amount=rent_mtd,
            category="Rent",
            txn_date=date(today.year, today.month, min(2, today.day)),
            is_recurring=False,
        )
        db.add(t_rent)
        txns.append(t_rent)
    if rem_mtd > Decimal("0"):
        t_groc = Transaction(
            user_id=uid,
            type="expense",
            amount=rem_mtd,
            category="Groceries",
            txn_date=date(today.year, today.month, min(6, today.day)),
            is_recurring=False,
        )
        db.add(t_groc)
        txns.append(t_groc)

    liab = Liability(
        user_id=uid,
        type="education",
        lender_name="Education Loan Bank",
        outstanding_principal=Decimal("400000.00"),
        interest_rate=Decimal("8.50"),
        emi_amount=Decimal("12000.00"),
        due_day=10,
        remaining_months=40,
        status="active",
    )
    db.add(liab)
    db.flush()
    db.refresh(liab)
    rem_count = len(create_liability_reminders(liab, db, today))

    holdings = [
        Holding(
            user_id=uid,
            type="bank_savings",
            name="Savings account",
            current_value=Decimal("390000.00"),
            as_of_date=today,
            liquidity="liquid",
            is_emergency_reserve=True,
            source="manual",
        ),
        Holding(
            user_id=uid,
            type="fixed_deposit",
            name="Fixed deposit",
            current_value=Decimal("100000.00"),
            as_of_date=today,
            liquidity="semi_liquid",
            is_emergency_reserve=False,
            source="manual",
        ),
        Holding(
            user_id=uid,
            type="mutual_fund",
            name="Mutual fund",
            current_value=Decimal("240000.00"),
            as_of_date=today,
            liquidity="semi_liquid",
            is_emergency_reserve=False,
            source="manual",
        ),
        Holding(
            user_id=uid,
            type="gold",
            name="Gold",
            current_value=Decimal("60000.00"),
            as_of_date=today,
            liquidity="semi_liquid",
            is_emergency_reserve=False,
            source="manual",
        ),
    ]
    for h in holdings:
        db.add(h)

    goals = [
        Goal(
            user_id=uid,
            title="Europe trip",
            target_amount=Decimal("240000.00"),
            saved_amount=Decimal("60000.00"),
            target_date=_add_months(today, 12),
            priority="medium",
            liquidity_need="medium",
            status="active",
        ),
        Goal(
            user_id=uid,
            title="Home down payment",
            target_amount=Decimal("1200000.00"),
            saved_amount=Decimal("240000.00"),
            target_date=_add_months(today, 60),
            priority="high",
            liquidity_need="low",
            status="active",
        ),
    ]
    for g in goals:
        db.add(g)
    db.flush()
    for g in goals:
        db.refresh(g)
        rem_count += len(create_goal_reminders(g, db, today))

    # Score = 22 (moderate tolerance), horizon > 5 years (q1_horizon = 4)
    _save_risk_profile(
        db,
        user_id=uid,
        answers={
            "q1_horizon": 4,
            "q2_market_fall": 3,
            "q3_experience": 3,
            "q4_income_stability": 3,
            "q5_dependents": 3,
            "q6_essentials_share": 2,
            "q7_purpose": 2,
            "q8_volatility_comfort": 2,
        },
        income_sources=income_sources,
        txns=txns,
        liabilities=[liab],
        holdings=holdings,
        today=today,
    )

    appliance_specs = [
        (
            "Refrigerator",
            "Samsung refrigerator",
            "Samsung",
            Decimal("42999.00"),
            _add_months(today, -10),
            24,
        ),
        (
            "Washing Machine",
            "LG washing machine",
            "LG",
            Decimal("31500.00"),
            _add_months(today + timedelta(days=20), -24),
            24,
        ),
        ("AC", "Daikin AC", "Daikin", Decimal("38000.00"), _add_months(today, -30), 12),
        (
            "RO Purifier",
            "Kent RO purifier",
            "Kent",
            Decimal("14500.00"),
            _add_months(today, -5),
            12,
        ),
    ]
    svc_count = 0
    for cat_name, prod_name, brand, price, p_date, w_months in appliance_specs:
        _, s_cnt, r_cnt = _add_appliance_with_schedule(
            db,
            user_id=uid,
            categories_by_name=categories_by_name,
            category_name=cat_name,
            product_name=prod_name,
            brand=brand,
            price=price,
            purchase_date=p_date,
            warranty_months=w_months,
            today=today,
        )
        svc_count += s_cnt
        rem_count += r_cnt

    db.commit()
    return SeedSummary(
        name=user.name,
        email=user.email,
        income_sources=len(income_sources),
        transactions=len(txns),
        liabilities=1,
        holdings=len(holdings),
        goals=len(goals),
        appliances=len(appliance_specs),
        services=svc_count,
        reminders=rem_count,
    )


def _seed_isha(
    db: Session, categories_by_name: dict[str, ApplianceCategory], today: date
) -> SeedSummary:
    user = _upsert_demo_user(
        db,
        name="Isha25",
        email="isha25@vault.local",
        password="Isha@25",
    )
    uid = user.user_id

    inc_salary = IncomeSource(
        user_id=uid,
        name="Salary",
        amount=Decimal("55000.00"),
        frequency="monthly",
        income_type="fixed",
        expected_day=1,
        is_active=True,
    )
    inc_freelance = IncomeSource(
        user_id=uid,
        name="Freelance",
        amount=Decimal("5000.00"),
        frequency="monthly",
        income_type="variable",
        expected_day=15,
        is_active=True,
    )
    db.add(inc_salary)
    db.add(inc_freelance)
    income_sources = [inc_salary, inc_freelance]

    monthly_expenses: list[tuple[str, Decimal, int]] = [
        ("Rent", Decimal("15000.00"), 2),
        ("Groceries", Decimal("6000.00"), 6),
        ("Utilities", Decimal("2500.00"), 9),
        ("Transport", Decimal("3500.00"), 12),
        ("Health", Decimal("1000.00"), 15),
        ("Food-out", Decimal("6000.00"), 19),
        ("Entertainment", Decimal("3000.00"), 22),
        ("Shopping", Decimal("5000.00"), 26),
    ]
    txns = _add_monthly_expenses(db, uid, today, monthly_expenses)

    # Current month at ~125% of previous month's pace, with Shopping as the largest increase
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    days_elapsed = max(1, today.day)
    prev_total = sum((amt for _, amt, _ in monthly_expenses), Decimal("0"))
    target_mtd = _q2(prev_total * Decimal("1.25") * Decimal(days_elapsed) / Decimal(days_in_month))
    shopping_mtd = max(Decimal("5500.00"), _q2(target_mtd * Decimal("0.265306")))
    if shopping_mtd > target_mtd:
        shopping_mtd = target_mtd
    remaining_mtd = _q2(target_mtd - shopping_mtd)
    rent_mtd = min(Decimal("15000.00"), remaining_mtd)
    remaining_mtd = _q2(remaining_mtd - rent_mtd)
    groceries_mtd = min(Decimal("2000.00"), remaining_mtd)
    food_mtd = _q2(remaining_mtd - groceries_mtd)

    mtd_entries: list[tuple[str, Decimal, int]] = [
        ("Rent", rent_mtd, min(2, today.day)),
        ("Groceries", groceries_mtd, min(5, today.day)),
        ("Food-out", food_mtd, min(9, today.day)),
        ("Shopping", shopping_mtd, min(12, today.day)),
    ]
    for category, amount, day in mtd_entries:
        if amount > Decimal("0"):
            t = Transaction(
                user_id=uid,
                type="expense",
                amount=amount,
                category=category,
                txn_date=date(today.year, today.month, day),
                is_recurring=False,
            )
            db.add(t)
            txns.append(t)

    liab_cc = Liability(
        user_id=uid,
        type="credit_card",
        lender_name="Demo Card Bank",
        outstanding_principal=Decimal("120000.00"),
        interest_rate=Decimal("36.00"),
        emi_amount=Decimal("6000.00"),
        due_day=18,
        remaining_months=24,
        status="active",
    )
    liab_pl = Liability(
        user_id=uid,
        type="personal",
        lender_name="Personal Loan Bank",
        outstanding_principal=Decimal("150000.00"),
        interest_rate=Decimal("14.50"),
        emi_amount=Decimal("7000.00"),
        due_day=3,
        remaining_months=24,
        status="active",
    )
    liabilities = [liab_cc, liab_pl]
    for li in liabilities:
        db.add(li)
    db.flush()
    rem_count = 0
    for li in liabilities:
        db.refresh(li)
        rem_count += len(create_liability_reminders(li, db, today))

    holdings = [
        Holding(
            user_id=uid,
            type="bank_savings",
            name="Savings account",
            current_value=Decimal("40000.00"),
            as_of_date=today,
            liquidity="liquid",
            is_emergency_reserve=True,
            source="manual",
        ),
        Holding(
            user_id=uid,
            type="mutual_fund",
            name="Mutual fund",
            current_value=Decimal("25000.00"),
            as_of_date=today,
            liquidity="semi_liquid",
            is_emergency_reserve=False,
            source="manual",
        ),
    ]
    for h in holdings:
        db.add(h)

    goals = [
        Goal(
            user_id=uid,
            title="Laptop upgrade",
            target_amount=Decimal("80000.00"),
            saved_amount=Decimal("10000.00"),
            target_date=_add_months(today, 8),
            priority="high",
            liquidity_need="high",
            status="active",
        ),
        Goal(
            user_id=uid,
            title="Goa trip",
            target_amount=Decimal("45000.00"),
            saved_amount=Decimal("5000.00"),
            target_date=_add_months(today, 6),
            priority="low",
            liquidity_need="high",
            status="active",
        ),
    ]
    for g in goals:
        db.add(g)
    db.flush()
    for g in goals:
        db.refresh(g)
        rem_count += len(create_goal_reminders(g, db, today))

    # Score = 15 (conservative tolerance), horizon 3 to 5 years (q1_horizon = 3)
    _save_risk_profile(
        db,
        user_id=uid,
        answers={
            "q1_horizon": 3,
            "q2_market_fall": 2,
            "q3_experience": 2,
            "q4_income_stability": 2,
            "q5_dependents": 2,
            "q6_essentials_share": 2,
            "q7_purpose": 1,
            "q8_volatility_comfort": 1,
        },
        income_sources=income_sources,
        txns=txns,
        liabilities=liabilities,
        holdings=holdings,
        today=today,
    )

    appliance_specs = [
        (
            "Geyser",
            "Havells geyser",
            "Havells",
            Decimal("8990.00"),
            _add_months(today + timedelta(days=10), -12),
            12,
        ),
        ("AC", "Voltas AC", "Voltas", Decimal("36490.00"), _add_months(today, -3), 12),
        (
            "Washing Machine",
            "Whirlpool washing machine",
            "Whirlpool",
            Decimal("18990.00"),
            _add_months(today, -14),
            12,
        ),
    ]
    svc_count = 0
    for cat_name, prod_name, brand, price, p_date, w_months in appliance_specs:
        _, s_cnt, r_cnt = _add_appliance_with_schedule(
            db,
            user_id=uid,
            categories_by_name=categories_by_name,
            category_name=cat_name,
            product_name=prod_name,
            brand=brand,
            price=price,
            purchase_date=p_date,
            warranty_months=w_months,
            today=today,
        )
        svc_count += s_cnt
        rem_count += r_cnt

    db.commit()
    return SeedSummary(
        name=user.name,
        email=user.email,
        income_sources=len(income_sources),
        transactions=len(txns),
        liabilities=len(liabilities),
        holdings=len(holdings),
        goals=len(goals),
        appliances=len(appliance_specs),
        services=svc_count,
        reminders=rem_count,
    )


def seed_demo_ledgers(
    db: Session,
    *,
    only: str | None = None,
    today: date | None = None,
) -> list[SeedSummary]:
    """Idempotently seed Vartika24 and/or Isha25 demo ledgers."""
    ref_today = today or date.today()
    seed_service_intervals(db)
    categories_by_name = {c.name: c for c in db.query(ApplianceCategory).all()}

    targets = [only.lower()] if only else ["vartika", "isha"]
    summaries: list[SeedSummary] = []
    for target in targets:
        if target == "vartika":
            summaries.append(_seed_vartika(db, categories_by_name, ref_today))
        elif target == "isha":
            summaries.append(_seed_isha(db, categories_by_name, ref_today))
        else:
            raise ValueError(f"Unknown --only target: {target}")
    return summaries


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Seed Vartika24 and Isha25 demo ledgers.")
    parser.add_argument(
        "--only",
        choices=["vartika", "isha"],
        default=None,
        help="Seed only one demo ledger (vartika or isha).",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete and recreate the selected demo user data (default behavior).",
    )
    parser.add_argument(
        "--today",
        type=date.fromisoformat,
        default=None,
        help="Reference date YYYY-MM-DD (defaults to today).",
    )
    args = parser.parse_args(argv)

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        summaries = seed_demo_ledgers(session, only=args.only, today=args.today)
        for s in summaries:
            print(
                f"Seeded {s.name} ({s.email}): "
                f"{s.income_sources} income, {s.transactions} txns, "
                f"{s.liabilities} liabilities, {s.holdings} holdings, "
                f"{s.goals} goals, {s.appliances} appliances, "
                f"{s.services} services, {s.reminders} reminders."
            )


if __name__ == "__main__":
    main()
