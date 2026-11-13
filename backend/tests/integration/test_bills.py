"""FR-2, FR-3, FR-4: Integration tests for bill upload and retrieval."""

from __future__ import annotations

import io
from pathlib import Path

from fastapi.testclient import TestClient

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures"


def _pdf_bytes() -> bytes:
    """Load the sample PDF fixture."""
    path = FIXTURE_DIR / "sample_bill.pdf"
    return path.read_bytes()


def test_fr2_upload_bill_success(client: TestClient, auth_headers: dict[str, str]) -> None:
    """FR-2, FR-3: Upload valid PDF returns 201 with extraction fields."""
    files = {"file": ("sample_bill.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")}
    response = client.post("/bills", files=files, headers=auth_headers)
    assert response.status_code == 201, response.text
    data = response.json()
    assert "bill_id" in data
    assert data["file_type"] == "pdf"
    assert data["parse_status"] in ("parsed", "needs_review", "pending")
    assert "extraction_json" in data


def test_fr2_upload_bill_invalid_type(client: TestClient, auth_headers: dict[str, str]) -> None:
    """FR-2: Upload of invalid type (.txt) returns 422."""
    files = {"file": ("bill.txt", io.BytesIO(b"invoice data"), "text/plain")}
    response = client.post("/bills", files=files, headers=auth_headers)
    assert response.status_code == 422


def test_fr2_upload_bill_too_large(client: TestClient, auth_headers: dict[str, str]) -> None:
    """FR-2: Upload of file over 10 MB returns 422."""
    large_data = b"0" * (10 * 1024 * 1024 + 1)  # 10MB + 1 byte
    files = {"file": ("big.pdf", io.BytesIO(large_data), "application/pdf")}
    response = client.post("/bills", files=files, headers=auth_headers)
    assert response.status_code == 422


def test_fr2_get_bill_own(client: TestClient, auth_headers: dict[str, str]) -> None:
    """FR-2: User can retrieve their own bill."""
    files = {"file": ("sample_bill.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")}
    upload_resp = client.post("/bills", files=files, headers=auth_headers)
    assert upload_resp.status_code == 201
    bill_id = upload_resp.json()["bill_id"]

    get_resp = client.get(f"/bills/{bill_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["bill_id"] == bill_id


def test_nfr3_get_bill_other_user(
    client: TestClient,
    auth_headers: dict[str, str],
    db_session: object,
) -> None:
    """NFR-3: User B cannot access User A's bill (expect 404)."""
    import uuid
    from datetime import UTC, datetime

    from sqlalchemy.orm import Session

    from app.core.security import create_access_token, hash_password
    from app.models.user import User

    db: Session = db_session  # type: ignore[assignment]

    # Create user B
    email_b = f"userb_{uuid.uuid4().hex[:6]}@example.com"
    user_b = User(
        name="User B",
        email=email_b,
        password_hash=hash_password("Password123!"),
        consent_given_at=datetime.now(UTC),
    )
    db.add(user_b)
    db.commit()
    db.refresh(user_b)
    headers_b = {"Authorization": f"Bearer {create_access_token(subject=user_b.user_id)}"}

    # User A uploads a bill
    files = {"file": ("sample_bill.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")}
    upload_resp = client.post("/bills", files=files, headers=auth_headers)
    bill_id = upload_resp.json()["bill_id"]

    # User B tries to access it
    resp = client.get(f"/bills/{bill_id}", headers=headers_b)
    assert resp.status_code == 404


def test_fr4_correct_bill(client: TestClient, auth_headers: dict[str, str]) -> None:
    """FR-4: User can correct extracted fields; parse_status becomes 'corrected'."""
    files = {"file": ("sample_bill.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")}
    upload_resp = client.post("/bills", files=files, headers=auth_headers)
    bill_id = upload_resp.json()["bill_id"]

    correct_payload = {
        "corrected_fields": {
            "product_name": "Samsung AC",
            "price": "42500",
        }
    }
    resp = client.patch(f"/bills/{bill_id}/correct", json=correct_payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["parse_status"] == "corrected"
    assert data["corrected_fields"] is not None
