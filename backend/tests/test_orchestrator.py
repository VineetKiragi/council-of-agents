"""Unit tests for DeliberationOrchestrator.

Tests that touch the database require the test database to be set up first.
See conftest.py for instructions.
"""

from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session as DbSession

from backend.app.agents.agent_config import get_agent_configs
from backend.app.agents.base import BaseAgent
from backend.app.core.orchestrator import DeliberationOrchestrator
from backend.app.db.models import Message, Session


# ---------------------------------------------------------------------------
# Mock agent — no real API calls
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


def _make_mock_agents() -> list[_MockAgent]:
    """Return 5 mock agents whose role/provider match the real agent configs."""
    configs = get_agent_configs()
    return [
        _MockAgent(
            agent_id=f"mock-{i}",
            role=cfg.role,
            pseudonym=f"placeholder-{i}",  # orchestrator will overwrite this
            provider_name=cfg.provider,
            model_name=cfg.model,
        )
        for i, cfg in enumerate(configs)
    ]


@pytest.fixture
def mock_agents() -> list[_MockAgent]:
    return _make_mock_agents()


@pytest.fixture
def orchestrator(db_session: DbSession, mock_agents: list[_MockAgent]):
    return DeliberationOrchestrator(db=db_session, agents=mock_agents)


# ---------------------------------------------------------------------------
# test_build_round_context — pure string formatting, no DB needed
# ---------------------------------------------------------------------------


def test_build_round_context():
    orc = DeliberationOrchestrator(db=MagicMock())

    msg_a = Message(agent_pseudonym="Agent A", content="This is my view.")
    msg_b = Message(agent_pseudonym="Agent B", content="I strongly disagree.")

    result = orc._build_round_context(
        messages=[msg_a, msg_b],
        current_pseudonym="Agent A",
        round_label="Round 1",
    )

    # Returns a plain string
    assert isinstance(result, str)

    # Current agent is marked with "(you)"
    assert "Agent A (you)" in result

    # Other agent is NOT marked with "(you)"
    assert "Agent B (you)" not in result

    # Content is present
    assert "This is my view." in result
    assert "I strongly disagree." in result

    # Role and provider are never included (anonymization holds)
    assert "Chairman" not in result
    assert "anthropic" not in result
    assert "openai" not in result
    assert "google" not in result


# ---------------------------------------------------------------------------
# Orchestrator integration tests — require the test database
# ---------------------------------------------------------------------------


async def test_orchestrator_creates_session(orchestrator: DeliberationOrchestrator, db_session: DbSession):
    session_id = await orchestrator.run_deliberation("Should AI be regulated?")

    session = db_session.get(Session, session_id)
    assert session is not None
    assert session.status == "completed"


async def test_orchestrator_creates_correct_number_of_messages(
    orchestrator: DeliberationOrchestrator, db_session: DbSession
):
    session_id = await orchestrator.run_deliberation("Should AI be regulated?")

    messages = (
        db_session.query(Message)
        .filter(Message.session_id == session_id)
        .all()
    )

    by_round: dict[int, list[Message]] = {}
    for msg in messages:
        by_round.setdefault(msg.round_number, []).append(msg)

    assert len(by_round[1]) == 4, "Round 1 should have 4 council messages"
    assert len(by_round[2]) == 4, "Round 2 should have 4 council messages"
    assert len(by_round[3]) == 4, "Round 3 should have 4 council messages"
    assert len(by_round[0]) == 1, "Round 0 should have 1 chairman synthesis"
    assert len(messages) == 13


async def test_orchestrator_assigns_pseudonyms(
    orchestrator: DeliberationOrchestrator, db_session: DbSession
):
    session_id = await orchestrator.run_deliberation("Should AI be regulated?")

    round1_messages = (
        db_session.query(Message)
        .filter(Message.session_id == session_id, Message.round_number == 1)
        .all()
    )

    pseudonyms = {msg.agent_pseudonym for msg in round1_messages}
    assert pseudonyms == {"Agent A", "Agent B", "Agent C", "Agent D"}
