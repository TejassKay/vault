from fastapi.testclient import TestClient


def test_nfr6_health_check_returns_ok(client: TestClient) -> None:
    """NFR-6 (Maintainability): Verify service health endpoint returns 200 and expected schema."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "Vault"
    assert data["version"] == "0.1.0"


def test_nfr6_api_v1_health_check_returns_ok(client: TestClient) -> None:
    """NFR-6 (Maintainability): Verify versioned API v1 health endpoint works."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_nfr5_api_docs_accessible(client: TestClient) -> None:
    """NFR-5 (Portability): Verify OpenAPI documentation endpoint is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_root_endpoint(client: TestClient) -> None:
    """Verify root discovery endpoint returns metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "Vault"
    assert "version" in data
    assert "health" in data
