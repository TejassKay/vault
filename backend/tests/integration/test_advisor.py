"""FR-21 to FR-26, FR-29, NFR-3: Integration tests for Advisor, Risk, and Capacity."""

from datetime import UTC, date, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.holding import Holding
from app.models.income_source import IncomeSource
from app.models.liability import Liability
from app.models.transaction import Transaction
from app.models.user import User


def test_fr22_risk_questionnaire_and_profile_flow(client: TestClient, auth_headers: dict[str, str]) -> None:
    # 1. Get questionnaire
    q_resp = client.get("/risk-questionnaire", headers=auth_headers)
    assert q_resp.status_code == 200
    questions = q_resp.json()["questions"]
    assert len(questions) == 8
    assert all("id" in q and len(q["options"]) == 4 for q in questions)

    # 2. Submit risk profile
    answers = {q["id"]: 3 for q in questions}
    post_resp = client.post("/risk-profile", json={"answers": answers}, headers=auth_headers)
    assert post_resp.status_code == 201, post_resp.text
    profile_data = post_resp.json()
    assert profile_data["score"] == 24
    assert profile_data["tolerance_level"] == "moderate"
    assert profile_data["effective_level"] in ("conservative", "moderate", "aggressive")

    # 3. Get latest risk profile
    get_resp = client.get("/risk-profile", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["risk_profile_id"] == profile_data["risk_profile_id"]


def test_fr21_investment_capacity_endpoint(
    client: TestClient, auth_headers: dict[str, str], test_user: User, db_session: Session
) -> None:
    # Set up some baseline financial records for test_user
    today = date.today()
    inc = IncomeSource(
        user_id=test_user.user_id,
        name="Salary",
        amount=85000,
        frequency="monthly",
        income_type="fixed",
        is_active=True,
    )
    db_session.add(inc)

    exp = Transaction(
        user_id=test_user.user_id,
        type="expense",
        amount=32000,
        category="Rent",
        txn_date=today,
    )
    db_session.add(exp)

    liab = Liability(
        user_id=test_user.user_id,
        type="personal",
        lender_name="Bank",
        outstanding_principal=240000,
        interest_rate=11.0,
        emi_amount=10000,
        due_day=5,
        status="active",
    )
    db_session.add(liab)

    holding = Holding(
        user_id=test_user.user_id,
        type="bank_savings",
        name="Emergency Account",
        current_value=45000,
        as_of_date=today,
        liquidity="liquid",
        is_emergency_reserve=True,
    )
    db_session.add(holding)
    db_session.commit()

    resp = client.get("/investment-capacity", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] in ("ok", "blocked")
    assert len(data["steps"]) >= 5
    assert len(data["assumptions"]) > 0


def test_fr23_to_fr26_recommendations_generate_list_patch(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    # 1. Generate recommendations
    gen_resp = client.post("/recommendations/generate", headers=auth_headers)
    assert gen_resp.status_code == 200, gen_resp.text
    gen_data = gen_resp.json()
    assert "recommendations" in gen_data
    assert "disclaimer" in gen_data
    assert "not investment advice" in gen_data["disclaimer"].lower()

    recs = gen_data["recommendations"]
    assert len(recs) > 0
    first_rec = recs[0]
    assert first_rec["status"] == "proposed"
    assert first_rec["explanation_text"] is not None
    assert first_rec["explanation_source"] in ("llm", "template")
    assert first_rec["priority_rank"] == 1
    rec_id = first_rec["recommendation_id"]

    # 2. Get recommendations
    get_resp = client.get("/recommendations", headers=auth_headers)
    assert get_resp.status_code == 200
    listed_recs = get_resp.json()["recommendations"]
    assert any(r["recommendation_id"] == rec_id for r in listed_recs)

    # 3. FR-26: User accepts recommendation
    patch_resp = client.patch(
        f"/recommendations/{rec_id}",
        json={"status": "accepted"},
        headers=auth_headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "accepted"
    assert patch_resp.json()["decided_at"] is not None


def test_nfr3_user_isolation_advisor(
    client: TestClient,
    auth_headers: dict[str, str],
    db_session: Session,
) -> None:
    """NFR-3: User 2 cannot access or patch User 1's recommendation."""
    # Create User 2 if not exists
    email2 = "user2_advisor@example.com"
    user2 = db_session.query(User).filter(User.email == email2).first()
    if not user2:
        user2 = User(
            name="User Two",
            email=email2,
            password_hash=hash_password("Pass123!"),
            consent_given_at=datetime.now(UTC),
        )
        db_session.add(user2)
        db_session.commit()
        db_session.refresh(user2)

    user2_token = create_access_token(subject=user2.user_id)
    user2_headers = {"Authorization": f"Bearer {user2_token}"}

    # Generate recommendation for User 1
    gen_resp = client.post("/recommendations/generate", headers=auth_headers)
    user1_rec_id = gen_resp.json()["recommendations"][0]["recommendation_id"]

    # User 2 tries to patch User 1's recommendation -> expect 404
    patch_resp = client.patch(
        f"/recommendations/{user1_rec_id}",
        json={"status": "rejected"},
        headers=user2_headers,
    )
    assert patch_resp.status_code == 404
