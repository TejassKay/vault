"""Integration tests for Vartika24 and Isha25 demo ledgers (Task 2)."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.engines.budget_engine import compute_budget_nudge
from app.models.appliance import Appliance
from app.models.goal import Goal
from app.models.holding import Holding
from app.models.income_source import IncomeSource
from app.models.liability import Liability
from app.models.reminder import Reminder
from app.models.risk_profile import RiskProfile
from app.models.transaction import Transaction
from app.models.user import User
from app.seed.demo_ledgers import seed_demo_ledgers

REF_TODAY = date(2026, 11, 14)


class _FixedDate(date):
    @classmethod
    def today(cls) -> _FixedDate:
        return cls(REF_TODAY.year, REF_TODAY.month, REF_TODAY.day)


def _auth_headers_for(user: User) -> dict[str, str]:
    token = create_access_token(subject=user.user_id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def fixed_today(monkeypatch: pytest.MonkeyPatch) -> None:
    import app.api.routers.advisor as advisor_router
    import app.api.routers.dashboard as dashboard_router
    import app.api.routers.finance as finance_router
    import app.api.routers.goals as goals_router

    monkeypatch.setattr(finance_router, "date", _FixedDate)
    monkeypatch.setattr(advisor_router, "date", _FixedDate)
    monkeypatch.setattr(dashboard_router, "date", _FixedDate)
    monkeypatch.setattr(goals_router, "date", _FixedDate)


def test_demo_ledgers_vartika24_and_isha25_endpoints(
    client: TestClient,
    db_session: Session,
    fixed_today: None,
) -> None:
    """Seed with --today 2026-11-14 and verify snapshot, capacity, recommendations, timeline."""
    seed_demo_ledgers(db_session, today=REF_TODAY)

    vartika = db_session.query(User).filter(User.email == "vartika24@vault.local").one()
    isha = db_session.query(User).filter(User.email == "isha25@vault.local").one()

    v_headers = _auth_headers_for(vartika)
    i_headers = _auth_headers_for(isha)

    # --- Vartika24 ---
    v_snap = client.get("/snapshot", headers=v_headers)
    assert v_snap.status_code == 200
    vs = v_snap.json()
    assert Decimal(str(vs["monthly_income"])) == Decimal("120000.00")
    assert Decimal(str(vs["essential_expenses"])) == Decimal("48000.00")
    assert Decimal(str(vs["discretionary_expenses"])) == Decimal("20000.00")
    assert Decimal(str(vs["debt_payments"])) == Decimal("12000.00")
    assert Decimal(str(vs["net_cash_flow"])) == Decimal("40000.00")
    assert Decimal(str(vs["savings_rate"])) == Decimal("33.33")
    assert Decimal(str(vs["dti"])) == Decimal("10.00")
    assert Decimal(str(vs["net_worth"])) == Decimal("390000.00")
    assert Decimal(str(vs["emergency_coverage_months"])) == Decimal("6.50")

    v_goals = client.get("/goals", headers=v_headers).json()
    v_contribs: dict[str, Decimal] = {}
    for g in v_goals:
        proj = client.get(f"/goals/{g['goal_id']}/projection", headers=v_headers).json()
        v_contribs[g["title"]] = Decimal(str(proj["planning_contribution"]))
    assert v_contribs["Europe trip"] == Decimal("15000.00")
    assert v_contribs["Home down payment"] == Decimal("16000.00")
    assert sum(v_contribs.values()) == Decimal("31000.00")

    v_cap_resp = client.get("/investment-capacity", headers=v_headers)
    assert v_cap_resp.status_code == 200
    vc = v_cap_resp.json()
    assert vc["status"] == "ok"
    assert Decimal(str(vc["capacity"])) == Decimal("8100.00")
    assert vc["reason_codes"] == []
    assert Decimal(str(vc["emergency_top_up"])) == Decimal("0.00")

    v_risk = client.get("/risk-profile", headers=v_headers).json()
    assert v_risk["effective_level"] == "moderate"

    v_rec_resp = client.post("/recommendations/generate", headers=v_headers)
    assert v_rec_resp.status_code == 200
    v_recs = v_rec_resp.json()["recommendations"]
    assert [r["rec_type"] for r in v_recs] == ["INVEST_BY_CATEGORY", "REVIEW_SCHEDULE"]

    v_alloc = v_recs[0]["inputs_snapshot"]["allocation"]
    assert Decimal(str(v_alloc["equity"])) == Decimal("4050.00")
    assert Decimal(str(v_alloc["debt"])) == Decimal("2835.00")
    assert Decimal(str(v_alloc["gold"])) == Decimal("810.00")
    assert Decimal(str(v_alloc["liquid"])) == Decimal("405.00")

    v_tl = client.get("/timeline", headers=v_headers)
    assert v_tl.status_code == 200
    assert len(v_tl.json()["events"]) > 0

    # Budget nudge for Vartika24: none
    v_txns = db_session.query(Transaction).filter(Transaction.user_id == vartika.user_id).all()
    v_mtd = [
        (t.amount, t.category)
        for t in v_txns
        if t.type == "expense" and t.txn_date.year == 2026 and t.txn_date.month == 11
    ]
    v_prev = [
        (t.amount, t.category)
        for t in v_txns
        if t.type == "expense" and t.txn_date.year == 2026 and t.txn_date.month == 10
    ]
    v_nudge = compute_budget_nudge(v_mtd, v_prev, REF_TODAY)
    assert v_nudge.should_show is False

    # --- Isha25 ---
    i_snap = client.get("/snapshot", headers=i_headers)
    assert i_snap.status_code == 200
    is_ = i_snap.json()
    assert Decimal(str(is_["monthly_income"])) == Decimal("60000.00")
    assert Decimal(str(is_["essential_expenses"])) == Decimal("28000.00")
    assert Decimal(str(is_["discretionary_expenses"])) == Decimal("14000.00")
    assert Decimal(str(is_["debt_payments"])) == Decimal("13000.00")
    assert Decimal(str(is_["net_cash_flow"])) == Decimal("5000.00")
    assert Decimal(str(is_["savings_rate"])) == Decimal("8.33")
    assert Decimal(str(is_["dti"])) == Decimal("21.67")
    assert Decimal(str(is_["net_worth"])) == Decimal("-205000.00")
    assert Decimal(str(is_["emergency_coverage_months"])) == Decimal("0.98")

    i_goals = client.get("/goals", headers=i_headers).json()
    i_contribs: dict[str, Decimal] = {}
    for g in i_goals:
        proj = client.get(f"/goals/{g['goal_id']}/projection", headers=i_headers).json()
        i_contribs[g["title"]] = Decimal(str(proj["planning_contribution"]))
    assert i_contribs["Laptop upgrade"] == Decimal("8750.00")
    assert i_contribs["Goa trip"] == Decimal("6666.67")
    assert sum(i_contribs.values()) == Decimal("15416.67")

    i_cap_resp = client.get("/investment-capacity", headers=i_headers)
    assert i_cap_resp.status_code == 200
    ic = i_cap_resp.json()
    assert ic["status"] == "blocked"
    assert Decimal(str(ic["capacity"])) == Decimal("0.00")
    assert set(ic["reason_codes"]) == {"EMERGENCY_FUND_LOW", "HIGH_INTEREST_DEBT"}
    assert Decimal(str(ic["emergency_top_up"])) == Decimal("17166.67")

    i_risk = client.get("/risk-profile", headers=i_headers).json()
    assert i_risk["effective_level"] == "conservative"

    i_rec_resp = client.post("/recommendations/generate", headers=i_headers)
    assert i_rec_resp.status_code == 200
    i_recs = i_rec_resp.json()["recommendations"]
    assert [r["rec_type"] for r in i_recs] == [
        "HIGH_INTEREST_DEBT",
        "EMERGENCY_FUND_LOW",
        "GOALS_UNDERFUNDED",
        "REVIEW_SCHEDULE",
    ]
    goals_rec = next(r for r in i_recs if r["rec_type"] == "GOALS_UNDERFUNDED")
    assert Decimal(str(goals_rec["inputs_snapshot"]["shortfall"])) == Decimal("10416.67")

    i_tl = client.get("/timeline", headers=i_headers)
    assert i_tl.status_code == 200
    assert len(i_tl.json()["events"]) > 0

    # Budget nudge for Isha25: on track to exceed, naming Shopping
    i_txns = db_session.query(Transaction).filter(Transaction.user_id == isha.user_id).all()
    i_mtd = [
        (t.amount, t.category)
        for t in i_txns
        if t.type == "expense" and t.txn_date.year == 2026 and t.txn_date.month == 11
    ]
    i_prev = [
        (t.amount, t.category)
        for t in i_txns
        if t.type == "expense" and t.txn_date.year == 2026 and t.txn_date.month == 10
    ]
    i_nudge = compute_budget_nudge(i_mtd, i_prev, REF_TODAY)
    assert i_nudge.should_show is True
    assert i_nudge.message is not None and "on track to exceed" in i_nudge.message.lower()
    assert i_nudge.largest_category_increase == "Shopping"
    assert "Shopping" in i_nudge.message


def test_demo_ledgers_idempotent_and_tejas23_untouched(db_session: Session) -> None:
    """Running seed twice creates no duplicates and never modifies Tejas23."""
    tejas = db_session.query(User).filter(User.name == "Tejas23").first()
    if not tejas:
        tejas = User(
            name="Tejas23",
            email="tejas23_guard@vault.local",
            password_hash=hash_password("Tejas@23"),
            consent_given_at=datetime.now(UTC),
        )
        db_session.add(tejas)
        db_session.flush()
        db_session.add(
            IncomeSource(
                user_id=tejas.user_id,
                name="Tejas Salary",
                amount=Decimal("95000.00"),
                frequency="monthly",
                income_type="fixed",
                is_active=True,
            )
        )
        db_session.commit()

    tejas_id = tejas.user_id
    tejas_inc_before = (
        db_session.query(IncomeSource).filter(IncomeSource.user_id == tejas_id).count()
    )

    seed_demo_ledgers(db_session, today=REF_TODAY)
    vartika = db_session.query(User).filter(User.email == "vartika24@vault.local").one()
    v_counts_1 = (
        db_session.query(IncomeSource).filter(IncomeSource.user_id == vartika.user_id).count(),
        db_session.query(Transaction).filter(Transaction.user_id == vartika.user_id).count(),
        db_session.query(Liability).filter(Liability.user_id == vartika.user_id).count(),
        db_session.query(Holding).filter(Holding.user_id == vartika.user_id).count(),
        db_session.query(Goal).filter(Goal.user_id == vartika.user_id).count(),
        db_session.query(Appliance).filter(Appliance.user_id == vartika.user_id).count(),
        db_session.query(RiskProfile).filter(RiskProfile.user_id == vartika.user_id).count(),
        db_session.query(Reminder).filter(Reminder.user_id == vartika.user_id).count(),
    )

    # Second run
    seed_demo_ledgers(db_session, today=REF_TODAY)
    v_counts_2 = (
        db_session.query(IncomeSource).filter(IncomeSource.user_id == vartika.user_id).count(),
        db_session.query(Transaction).filter(Transaction.user_id == vartika.user_id).count(),
        db_session.query(Liability).filter(Liability.user_id == vartika.user_id).count(),
        db_session.query(Holding).filter(Holding.user_id == vartika.user_id).count(),
        db_session.query(Goal).filter(Goal.user_id == vartika.user_id).count(),
        db_session.query(Appliance).filter(Appliance.user_id == vartika.user_id).count(),
        db_session.query(RiskProfile).filter(RiskProfile.user_id == vartika.user_id).count(),
        db_session.query(Reminder).filter(Reminder.user_id == vartika.user_id).count(),
    )
    assert v_counts_1 == v_counts_2

    tejas_after = db_session.query(User).filter(User.user_id == tejas_id).one()
    assert tejas_after.name == "Tejas23"
    assert (
        db_session.query(IncomeSource).filter(IncomeSource.user_id == tejas_id).count()
        == tejas_inc_before
    )
