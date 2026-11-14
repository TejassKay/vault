"""FR-11, FR-12, FR-28, FR-30, Spec 6.6: Integration tests for Dashboard, Timeline, Export, Delete, and Demo Seed."""

from datetime import UTC, date, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.holding import Holding
from app.models.income_source import IncomeSource
from app.models.liability import Liability
from app.models.transaction import Transaction
from app.models.user import User


def test_fr11_dashboard_and_timeline_endpoints(client: TestClient, db_session: Session) -> None:
    today = date.today()
    # Create isolated user with uuid to ensure zero data collisions across runs
    import uuid

    email = f"dash_user_{uuid.uuid4().hex[:8]}@vault.local"
    user = User(
        name="Dash User",
        email=email,
        password_hash=hash_password("Pass123!"),
        consent_given_at=datetime.now(UTC),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    uid = user.user_id
    token = create_access_token(subject=uid)
    headers = {"Authorization": f"Bearer {token}"}

    # Add sample data
    db_session.add(
        IncomeSource(
            user_id=uid,
            name="Job Salary",
            amount=85000,
            frequency="monthly",
            income_type="fixed",
            is_active=True,
        )
    )
    db_session.add(
        Transaction(
            user_id=uid,
            type="expense",
            amount=32000,
            category="Rent",
            txn_date=today,
        )
    )
    db_session.add(
        Liability(
            user_id=uid,
            type="personal",
            lender_name="Bank",
            outstanding_principal=240000,
            interest_rate=11.0,
            emi_amount=10000,
            due_day=5,
            status="active",
        )
    )
    db_session.add(
        Holding(
            user_id=uid,
            type="bank_savings",
            name="Emergency Reserve",
            current_value=45000,
            as_of_date=today,
            liquidity="liquid",
            is_emergency_reserve=True,
        )
    )
    db_session.commit()

    # 1. GET /dashboard (FR-11)
    dash_resp = client.get("/dashboard", headers=headers)
    assert dash_resp.status_code == 200, dash_resp.text
    dash_data = dash_resp.json()
    assert "snapshot" in dash_data
    assert dash_data["snapshot"]["monthly_income"] == "85000.00"
    assert "upcoming_obligations" in dash_data
    assert "freshness" in dash_data
    assert "physical_assets_estimate" in dash_data

    # 2. GET /timeline (FR-12)
    time_resp = client.get("/timeline", headers=headers)
    assert time_resp.status_code == 200, time_resp.text
    time_data = time_resp.json()
    assert "events" in time_data
    assert any(e["event_type"] == "emi" for e in time_data["events"])


def test_fr30_export_and_delete_account(client: TestClient, db_session: Session) -> None:
    """FR-30: Export user data and delete account with all cascade records."""
    # Create distinct user for deletion test
    email = "delete_me@vault.local"
    user = db_session.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            name="Delete Target",
            email=email,
            password_hash=hash_password("Pass123!"),
            consent_given_at=datetime.now(UTC),
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

    uid = user.user_id
    token = create_access_token(subject=uid)
    headers = {"Authorization": f"Bearer {token}"}

    # Add holding
    db_session.add(
        Holding(
            user_id=uid,
            type="bank_savings",
            name="Delete Holding",
            current_value=12000,
            as_of_date=date.today(),
            liquidity="liquid",
        )
    )
    db_session.commit()

    # 1. Export (FR-30)
    exp_resp = client.get("/me/export", headers=headers)
    assert exp_resp.status_code == 200, exp_resp.text
    export_data = exp_resp.json()
    assert export_data["user"]["email"] == email
    assert len(export_data["holdings"]) == 1
    assert export_data["holdings"][0]["name"] == "Delete Holding"

    # 2. Delete (FR-30)
    del_resp = client.delete("/me", headers=headers)
    assert del_resp.status_code == 204

    # Verify user and cascaded holdings deleted from DB
    deleted_user = db_session.query(User).filter(User.user_id == uid).first()
    assert deleted_user is None
    deleted_holdings = db_session.query(Holding).filter(Holding.user_id == uid).all()
    assert len(deleted_holdings) == 0


def test_spec_6_6_demo_seed_and_scenario_switch(client: TestClient) -> None:
    """Part 7.4 & Spec 6.6: POST /demo/seed for Scenario A and Scenario B."""
    # Seed Scenario A
    resp_a = client.post("/demo/seed", json={"scenario": "A"})
    assert resp_a.status_code == 200, resp_a.text
    data_a = resp_a.json()
    assert data_a["scenario"] == "A"
    assert data_a["user_email"] == "demo@vault.local"

    # Seed Scenario B
    resp_b = client.post("/demo/seed", json={"scenario": "B"})
    assert resp_b.status_code == 200, resp_b.text
    data_b = resp_b.json()
    assert data_b["scenario"] == "B"
