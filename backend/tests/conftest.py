from collections.abc import Generator
from datetime import UTC

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.user import User


@pytest.fixture(scope="session")
def db_session() -> Generator[Session, None, None]:
    """Database session fixture."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Test client fixture for FastAPI app with DB dependency override."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Fixture providing a test user."""
    email = "testuser@example.com"
    user = db_session.query(User).filter(User.email == email).first()
    if not user:
        from datetime import datetime

        user = User(
            name="Test User",
            email=email,
            password_hash=hash_password("Password123!"),
            consent_given_at=datetime.now(UTC),
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    """Fixture providing authorization bearer headers for test_user."""
    token = create_access_token(subject=test_user.user_id)
    return {"Authorization": f"Bearer {token}"}
