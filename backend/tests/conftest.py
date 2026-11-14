from collections.abc import Generator
from datetime import UTC, date, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.holding import Holding
from app.models.income_source import IncomeSource
from app.models.liability import Liability
from app.models.transaction import Transaction
from app.models.user import User
from app.seed.seed_intervals import seed_service_intervals

# Test engine using app settings (respects DATABASE_URL)
test_engine = create_engine(
    settings.sync_database_url,
    pool_pre_ping=True,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database() -> Generator[None, None, None]:
    """Ensure all database tables and base reference data exist for the test session."""
    Base.metadata.create_all(bind=test_engine)
    with TestingSessionLocal() as session:
        seed_service_intervals(session)
    yield


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide a transactional database session per test that always rolls back.

    Uses an external transaction connection with nested SAVEPOINT so that
    commits inside application endpoints only release savepoints, and the entire
    transaction is safely rolled back during teardown (even if tests or endpoints fail).
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Begin nested savepoint
    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def end_savepoint(session_obj, trans):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()


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
    """Fixture providing a test user with baseline financial records."""
    email = "testuser@example.com"
    user = db_session.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            name="Test User",
            email=email,
            password_hash=hash_password("Password123!"),
            consent_given_at=datetime.now(UTC),
        )
        db_session.add(user)
        db_session.flush()
        db_session.refresh(user)

        # Baseline records for advisor and financial calculation consistency across rolled back tests
        today = date.today()
        inc = IncomeSource(
            user_id=user.user_id,
            name="Salary",
            amount=85000,
            frequency="monthly",
            income_type="fixed",
            is_active=True,
        )
        exp = Transaction(
            user_id=user.user_id,
            type="expense",
            amount=32000,
            category="Rent",
            txn_date=today,
        )
        liab = Liability(
            user_id=user.user_id,
            type="personal",
            lender_name="Bank",
            outstanding_principal=240000,
            interest_rate=11.0,
            emi_amount=10000,
            due_day=5,
            status="active",
        )
        holding = Holding(
            user_id=user.user_id,
            type="bank_savings",
            name="Emergency Account",
            current_value=45000,
            as_of_date=today,
            liquidity="liquid",
            is_emergency_reserve=True,
        )
        db_session.add_all([inc, exp, liab, holding])
        db_session.flush()

    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    """Fixture providing authorization bearer headers for test_user."""
    token = create_access_token(subject=test_user.user_id)
    return {"Authorization": f"Bearer {token}"}
