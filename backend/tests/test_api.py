"""Integration tests for REST API endpoints.

Uses the TestClient + test database — no real LLM API calls.
Sessions and messages are built directly via SQLAlchemy (db_session.add + flush)
so each test is focused on exactly one endpoint.
"""

import uuid

import pytest
from sqlalchemy.orm import Session as DbSession
from starlette.testclient import TestClient

from backend.app.db.models import Message, Session


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _session(status: str = "completed", prompt: str = "Is AI safe?") -> Session:
    return Session(id=uuid.uuid4(), prompt=prompt, status=status)


def _message(session_id: uuid.UUID, **overrides) -> Message:
    fields = {
        "id": uuid.uuid4(),
        "session_id": session_id,
        "round_number": 1,
        "agent_pseudonym": "Agent A",
        "agent_role": "Analytical",
        "agent_provider": "openai",
        "content": "This is a test response.",
        "token_usage": 100,
        "latency_ms": 200,
    }
    fields.update(overrides)
    return Message(**fields)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


def test_health_endpoint(client: TestClient):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


# ---------------------------------------------------------------------------
# List sessions
# ---------------------------------------------------------------------------


def test_list_sessions_empty(client: TestClient):
    resp = client.get("/api/sessions")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_sessions_with_data(client: TestClient, db_session: DbSession):
    s = _session(prompt="Should AI be regulated?", status="completed")
    db_session.add(s)
    db_session.flush()

    resp = client.get("/api/sessions")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["prompt"] == "Should AI be regulated?"
    assert data[0]["status"] == "completed"


# ---------------------------------------------------------------------------
# Get session by ID
# ---------------------------------------------------------------------------


def test_get_session_by_id(client: TestClient, db_session: DbSession):
    s = _session()
    db_session.add(s)
    db_session.flush()

    db_session.add(_message(s.id, agent_pseudonym="Agent A", round_number=1))
    db_session.add(_message(s.id, agent_pseudonym="Agent B", round_number=2))
    db_session.flush()

    resp = client.get(f"/api/sessions/{s.id}")
    assert resp.status_code == 200
    data = resp.json()

    assert data["id"] == str(s.id)
    assert data["prompt"] == s.prompt
    assert len(data["messages"]) == 2

    # Anonymization contract: role and provider must be absent during deliberation view
    for msg in data["messages"]:
        assert "agent_role" not in msg
        assert "agent_provider" not in msg


def test_get_session_not_found(client: TestClient):
    resp = client.get(f"/api/sessions/{uuid.uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Reveal endpoint
# ---------------------------------------------------------------------------


def test_reveal_endpoint(client: TestClient, db_session: DbSession):
    s = _session(status="completed")
    db_session.add(s)
    db_session.flush()

    db_session.add(_message(s.id, agent_role="Devil's Advocate", agent_provider="openai"))
    db_session.flush()

    resp = client.get(f"/api/sessions/{s.id}/reveal")
    assert resp.status_code == 200
    data = resp.json()

    # Same data, different endpoint — role and provider now visible
    assert len(data["messages"]) == 1
    msg = data["messages"][0]
    assert msg["agent_role"] == "Devil's Advocate"
    assert msg["agent_provider"] == "openai"


def test_reveal_rejects_in_progress(client: TestClient, db_session: DbSession):
    s = _session(status="in_progress")
    db_session.add(s)
    db_session.flush()

    resp = client.get(f"/api/sessions/{s.id}/reveal")
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Stats endpoint
# ---------------------------------------------------------------------------


def test_stats_endpoint(client: TestClient, db_session: DbSession):
    s = _session(status="completed")
    db_session.add(s)
    db_session.flush()

    db_session.add(_message(s.id, agent_pseudonym="Agent A", agent_provider="openai",    token_usage=100, latency_ms=200))
    db_session.add(_message(s.id, agent_pseudonym="Agent B", agent_provider="anthropic", token_usage=150, latency_ms=300))
    db_session.flush()

    resp = client.get(f"/api/sessions/{s.id}/stats")
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_tokens"] == 250
    assert "estimated_cost" in data
    assert data["estimated_cost"] > 0
    assert isinstance(data["per_agent"], list)
    assert len(data["per_agent"]) == 2
    assert {a["pseudonym"] for a in data["per_agent"]} == {"Agent A", "Agent B"}
