"""Shared fixtures for the backend test suite."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from backend.app.agents.base import BaseAgent
from backend.app.config import settings
from backend.app.db.database import Base, get_db
from backend.app.main import app

# ---------------------------------------------------------------------------
# Test database
# NOTE: Create this database once before running tests for the first time:
#   psql -U council_user -d postgres \
#     -c "CREATE DATABASE council_of_agents_test OWNER council_user;"
# ---------------------------------------------------------------------------
_TEST_DATABASE_URL = str(settings.DATABASE_URL).rsplit("/", 1)[0] + "/council_of_agents_test"


# ---------------------------------------------------------------------------
# db_engine — session-scoped: create tables once, drop after all tests finish
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(_TEST_DATABASE_URL, pool_pre_ping=True)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


# ---------------------------------------------------------------------------
# db_session — function-scoped: each test runs inside a transaction that is
# rolled back afterwards, so tests never affect each other.
#
# Uses SQLAlchemy 2.0's join_transaction_mode="create_savepoint" so that any
# commit() calls inside route handlers create a savepoint rather than a real
# commit, keeping everything within the outer transaction we roll back.
# ---------------------------------------------------------------------------
@pytest.fixture
def db_session(db_engine):
    with db_engine.connect() as conn:
        with conn.begin() as txn:
            with Session(conn, join_transaction_mode="create_savepoint") as session:
                yield session
            txn.rollback()


# ---------------------------------------------------------------------------
# client — FastAPI TestClient wired to the test db_session.
# The get_db dependency is overridden to return the test session so that
# route handlers operate against the test database and participate in the
# per-test rollback.
# ---------------------------------------------------------------------------
@pytest.fixture
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# mock_agent — a BaseAgent subclass that returns a fixed response without
# making any real LLM API calls.
# ---------------------------------------------------------------------------
class _MockAgent(BaseAgent):
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1024,
    ) -> dict:
        return {
            "content": f"Mock response from {self.role}",
            "token_usage": 50,
            "latency_ms": 100,
        }


@pytest.fixture
def mock_agent():
    return _MockAgent(
        agent_id="mock-agent",
        role="Mock",
        pseudonym="Agent X",
        provider_name="mock",
        model_name="mock-model",
    )
