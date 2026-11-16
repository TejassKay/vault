import uuid

from fastapi.testclient import TestClient


def test_fr1_signup_with_consent(client: TestClient) -> None:
    """FR-1: User can sign up with name, email, password, and mandatory consent."""
    unique_email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "name": "Arjun Kumar",
        "email": unique_email,
        "password": "SecurePassword123!",
        "consent": True,
    }
    response = client.post("/auth/signup", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Arjun Kumar"
    assert data["email"] == unique_email
    assert "user_id" in data
    assert "consent_given_at" in data
    assert data["consent_given_at"] is not None


def test_fr1_signup_without_consent_rejected(client: TestClient) -> None:
    """FR-1: Signup is rejected with 400 if consent is not granted."""
    unique_email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "name": "No Consent User",
        "email": unique_email,
        "password": "SecurePassword123!",
        "consent": False,
    }
    response = client.post("/auth/signup", json=payload)
    assert response.status_code == 400
    assert "Consent to data processing is required" in response.json()["detail"]


def test_fr1_signup_duplicate_email_rejected(client: TestClient) -> None:
    """FR-1: Duplicate email signup is rejected with 400."""
    unique_email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "name": "First Register",
        "email": unique_email,
        "password": "SecurePassword123!",
        "consent": True,
    }
    resp1 = client.post("/auth/signup", json=payload)
    assert resp1.status_code == 201

    resp2 = client.post("/auth/signup", json=payload)
    assert resp2.status_code == 400
    assert "already registered" in resp2.json()["detail"]


def test_fr1_login_success(client: TestClient) -> None:
    """FR-1 & NFR-3: User can log in with email/password and receive a JWT token."""
    unique_email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "CorrectPassword123!"
    client.post(
        "/auth/signup",
        json={"name": "Login Test", "email": unique_email, "password": password, "consent": True},
    )

    login_resp = client.post("/auth/login", json={"email": unique_email, "password": password})
    assert login_resp.status_code == 200
    data = login_resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


def test_fr1_login_invalid_credentials_fails(client: TestClient) -> None:
    """FR-1: Login fails with 401 when given invalid password."""
    unique_email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/auth/signup",
        json={
            "name": "Bad Login Test",
            "email": unique_email,
            "password": "CorrectPassword123!",
            "consent": True,
        },
    )

    login_resp = client.post(
        "/auth/login", json={"email": unique_email, "password": "WrongPassword123!"}
    )
    assert login_resp.status_code == 401
    assert "Invalid email or password" in login_resp.json()["detail"]


def test_nfr3_me_unauthenticated_fails(client: TestClient) -> None:
    """NFR-3: Accessing /me without JWT token returns 401."""
    response = client.get("/me")
    assert response.status_code == 401


def test_nfr3_me_authenticated_success(client: TestClient, auth_headers: dict[str, str]) -> None:
    """NFR-3: Accessing /me with valid JWT returns current user profile."""
    response = client.get("/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert "user_id" in data


def test_reset_user_data_clears_ledger_keeps_account(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    """POST /me/reset clears all ledger records while keeping the user account active."""
    reset_resp = client.post("/me/reset", headers=auth_headers)
    assert reset_resp.status_code == 204

    # Account still exists and is authenticated
    me_resp = client.get("/me", headers=auth_headers)
    assert me_resp.status_code == 200

    # All ledger collections are now empty
    assert client.get("/income-sources", headers=auth_headers).json() == []
    assert client.get("/transactions", headers=auth_headers).json() == []
    assert client.get("/liabilities", headers=auth_headers).json() == []
    assert client.get("/holdings", headers=auth_headers).json() == []
    assert client.get("/goals", headers=auth_headers).json() == []

    # User can immediately add new data after reset
    add_resp = client.post(
        "/income-sources",
        json={
            "name": "Fresh Salary",
            "amount": "50000.00",
            "frequency": "monthly",
            "income_type": "fixed",
            "is_active": True,
        },
        headers=auth_headers,
    )
    assert add_resp.status_code == 201
    assert len(client.get("/income-sources", headers=auth_headers).json()) == 1
