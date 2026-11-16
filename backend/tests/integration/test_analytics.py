"""Integration tests for GET /analytics/summary."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
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
    import app.api.routers.analytics as analytics_router

    monkeypatch.setattr(analytics_router, "date", _FixedDate)


def test_analytics_summary_demo_users(
    client: TestClient,
    db_session: Session,
    fixed_today: None,
) -> None:
    """Verify Vartika24 and Isha25 analytics summary with today = 2026-11-14."""
    seed_demo_ledgers(db_session, today=REF_TODAY)

    vartika = db_session.query(User).filter(User.email == "vartika24@vault.local").one()
    isha = db_session.query(User).filter(User.email == "isha25@vault.local").one()

    # --- Vartika24 ---
    v_resp = client.get("/analytics/summary?months=3", headers=_auth_headers_for(vartika))
    assert v_resp.status_code == 200
    v_data = v_resp.json()
    assert v_data["month"] == "2026-11"
    assert v_data["months"] == 3
    assert v_data["meta"]["has_data"] is True
    assert len(v_data["monthly_series"]) == 4

    # Last 3 full months: 2026-08, 2026-09, 2026-10
    for m in v_data["monthly_series"][:3]:
        assert Decimal(str(m["expenses"])) == Decimal("68000.00")
        assert Decimal(str(m["essential"])) == Decimal("48000.00")
        assert Decimal(str(m["discretionary"])) == Decimal("20000.00")

    # Rent 25,000 is the largest category
    v_top_cat = v_data["category_breakdown"]["items"][0]
    assert v_top_cat["category"] == "Rent"
    assert Decimal(str(v_top_cat["amount"])) == Decimal("25000.00")

    # --- Isha25 ---
    i_resp = client.get("/analytics/summary?months=3", headers=_auth_headers_for(isha))
    assert i_resp.status_code == 200
    i_data = i_resp.json()
    assert i_data["meta"]["has_data"] is True

    # Last 3 full months have expenses 42,000
    for m in i_data["monthly_series"][:3]:
        assert Decimal(str(m["expenses"])) == Decimal("42000.00")

    # Selected month shows Shopping with the largest delta
    assert i_data["compare"][0]["category"] == "Shopping"
    assert Decimal(str(i_data["compare"][0]["delta"])) > Decimal("0")


def test_analytics_summary_user_isolation_and_empty_user(
    client: TestClient,
    db_session: Session,
    fixed_today: None,
) -> None:
    """User A never sees User B's data, and an empty user returns has_data=False cleanly."""
    user_a = User(
        name="User A",
        email="analytics_a@example.com",
        password_hash=hash_password("Password123!"),
        consent_given_at=datetime.now(UTC),
    )
    user_b = User(
        name="User B",
        email="analytics_b@example.com",
        password_hash=hash_password("Password123!"),
        consent_given_at=datetime.now(UTC),
    )
    db_session.add_all([user_a, user_b])
    db_session.flush()

    db_session.add(
        Transaction(
            user_id=user_a.user_id,
            type="expense",
            amount=Decimal("12345.00"),
            category="Rent",
            txn_date=date(2026, 11, 2),
        )
    )
    db_session.flush()

    resp_b = client.get("/analytics/summary", headers=_auth_headers_for(user_b))
    assert resp_b.status_code == 200
    data_b = resp_b.json()
    assert data_b["meta"]["has_data"] is False
    assert Decimal(str(data_b["category_breakdown"]["total"])) == Decimal("0.00")
    assert data_b["category_breakdown"]["items"] == []

    resp_a = client.get("/analytics/summary", headers=_auth_headers_for(user_a))
    assert resp_a.status_code == 200
    data_a = resp_a.json()
    assert data_a["meta"]["has_data"] is True
    assert Decimal(str(data_a["category_breakdown"]["total"])) == Decimal("12345.00")


def test_analytics_summary_validation(
    client: TestClient,
    test_user: User,
) -> None:
    headers = _auth_headers_for(test_user)
    assert client.get("/analytics/summary?months=5", headers=headers).status_code == 422
    assert client.get("/analytics/summary?month=2026-13", headers=headers).status_code == 422
    assert client.get("/analytics/summary?month=invalid", headers=headers).status_code == 422
