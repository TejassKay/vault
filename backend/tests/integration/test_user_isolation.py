import uuid

from fastapi.testclient import TestClient

from app.core.security import create_access_token


def test_nfr3_user_data_isolation(client: TestClient) -> None:
    """NFR-3 & Ground Rule 7.2.6: Verify strict user isolation between two accounts."""
    # User A
    email_a = f"usera_{uuid.uuid4().hex[:8]}@example.com"
    resp_a = client.post(
        "/auth/signup",
        json={"name": "User Alpha", "email": email_a, "password": "PasswordA123!", "consent": True},
    )
    assert resp_a.status_code == 201
    user_a_id = resp_a.json()["user_id"]

    token_a_resp = client.post("/auth/login", json={"email": email_a, "password": "PasswordA123!"})
    token_a = token_a_resp.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # User B
    email_b = f"userb_{uuid.uuid4().hex[:8]}@example.com"
    resp_b = client.post(
        "/auth/signup",
        json={"name": "User Beta", "email": email_b, "password": "PasswordB123!", "consent": True},
    )
    assert resp_b.status_code == 201
    user_b_id = resp_b.json()["user_id"]

    token_b_resp = client.post("/auth/login", json={"email": email_b, "password": "PasswordB123!"})
    token_b = token_b_resp.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Verify User A's token only returns User A's profile
    me_a = client.get("/me", headers=headers_a)
    assert me_a.status_code == 200
    assert me_a.json()["user_id"] == user_a_id
    assert me_a.json()["email"] == email_a

    # Verify User B's token only returns User B's profile
    me_b = client.get("/me", headers=headers_b)
    assert me_b.status_code == 200
    assert me_b.json()["user_id"] == user_b_id
    assert me_b.json()["email"] == email_b

    # Verify User A cannot access with forged user ID token signed with wrong key
    tampered_token = create_access_token(subject=user_b_id) + "tampered"
    tampered_resp = client.get("/me", headers={"Authorization": f"Bearer {tampered_token}"})
    assert tampered_resp.status_code == 401
