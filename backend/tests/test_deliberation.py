"""End-to-end deliberation flow tests using mocked agents.

Covers the full lifecycle: session creation → 3 rounds → chairman synthesis.
No real LLM API calls — all agents return fixed responses instantly.
"""

from typing import Any

import pytest
from sqlalchemy.orm import Session as DbSession

from backend.app.agents.agent_config import get_agent_configs
from backend.app.agents.base import BaseAgent
from backend.app.core.orchestrator import DeliberationOrchestrator
from backend.app.db.models import Message, Session


# ---------------------------------------------------------------------------
# Mock agents
# ---------------------------------------------------------------------------


class _MockAgent(BaseAgent):
    """Returns a fixed successful response."""

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


class _FailingAgent(BaseAgent):
    """Always raises on generate() — simulates a broken provider."""

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1024,
    ) -> dict:
        raise RuntimeError("Simulated provider failure")


def _make_mock_agents() -> list[BaseAgent]:
    """5 mock agents built from real configs (role/provider accurate)."""
    configs = get_agent_configs()
    return [
        _MockAgent(
            agent_id=f"mock-{i}",
            role=cfg.role,
            pseudonym=f"placeholder-{i}",
            provider_name=cfg.provider,
            model_name=cfg.model,
        )
        for i, cfg in enumerate(configs)
    ]


def _make_agents_with_one_failure() -> list[BaseAgent]:
    """Same as above but agent at index 2 (Creative → 'Agent B') always fails."""
    agents = _make_mock_agents()
    cfg = get_agent_configs()[2]
    agents[2] = _FailingAgent(
        agent_id="mock-failing",
        role=cfg.role,
        pseudonym="placeholder-2",
        provider_name=cfg.provider,
        model_name=cfg.model,
    )
    return agents


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _messages_by_round(db_session: DbSession, session_id: Any) -> dict[int, list[Message]]:
    messages = (
        db_session.query(Message)
        .filter(Message.session_id == session_id)
        .all()
    )
    by_round: dict[int, list[Message]] = {}
    for msg in messages:
        by_round.setdefault(msg.round_number, []).append(msg)
    return by_round


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


async def test_full_deliberation_flow(db_session: DbSession):
    orc = DeliberationOrchestrator(db=db_session, agents=_make_mock_agents())
    session_id = await orc.run_deliberation("Test question")

    session = db_session.get(Session, session_id)
    assert session is not None
    assert session.status == "completed"
    assert session.final_decision  # not None and not empty

    by_round = _messages_by_round(db_session, session_id)
    assert len(by_round[1]) == 4
    assert len(by_round[2]) == 4
    assert len(by_round[3]) == 4
    assert len(by_round[0]) == 1


async def test_deliberation_messages_have_pseudonyms(db_session: DbSession):
    orc = DeliberationOrchestrator(db=db_session, agents=_make_mock_agents())
    session_id = await orc.run_deliberation("Test question")

    by_round = _messages_by_round(db_session, session_id)

    council_pseudonyms = {"Agent A", "Agent B", "Agent C", "Agent D"}
    for round_num in (1, 2, 3):
        for msg in by_round[round_num]:
            assert msg.agent_pseudonym in council_pseudonyms

    assert by_round[0][0].agent_pseudonym == "Chairman"


async def test_deliberation_stores_metadata(db_session: DbSession):
    orc = DeliberationOrchestrator(db=db_session, agents=_make_mock_agents())
    session_id = await orc.run_deliberation("Test question")

    all_messages = (
        db_session.query(Message)
        .filter(Message.session_id == session_id)
        .all()
    )

    assert len(all_messages) == 13
    for msg in all_messages:
        assert msg.token_usage is not None, f"token_usage missing on {msg.agent_pseudonym} r{msg.round_number}"
        assert msg.latency_ms is not None, f"latency_ms missing on {msg.agent_pseudonym} r{msg.round_number}"


async def test_deliberation_callback_fires(db_session: DbSession):
    fired: list[dict] = []

    async def _callback(data: dict) -> None:
        fired.append(data)

    orc = DeliberationOrchestrator(
        db=db_session,
        agents=_make_mock_agents(),
        callback=_callback,
    )
    await orc.run_deliberation("Test question")

    # 4 (round 1) + 4 (round 2) + 4 (round 3) + 1 (chairman) = 13
    assert len(fired) == 13

    # Callback payload matches the shape WebSocket clients receive
    for event in fired:
        assert "round_number" in event
        assert "agent_pseudonym" in event
        assert "content" in event


async def test_deliberation_continues_on_agent_failure(db_session: DbSession):
    # Agent at index 2 (Creative → pseudonym "Agent B") raises on every call
    orc = DeliberationOrchestrator(
        db=db_session,
        agents=_make_agents_with_one_failure(),
    )
    session_id = await orc.run_deliberation("Test question")

    session = db_session.get(Session, session_id)
    assert session.status == "completed", "Session should complete despite one failing agent"

    by_round = _messages_by_round(db_session, session_id)

    # Still 13 messages — failing agent produces error-content messages, not silence
    total = sum(len(msgs) for msgs in by_round.values())
    assert total == 13

    # Failing agent's messages contain error information
    agent_b_messages = [
        msg
        for msgs in by_round.values()
        for msg in msgs
        if msg.agent_pseudonym == "Agent B"
    ]
    assert len(agent_b_messages) == 3  # one per round
    for msg in agent_b_messages:
        assert "[" in msg.content and "error" in msg.content.lower()

    # Other council agents produced normal messages
    agent_a_messages = [
        msg for msgs in (by_round.get(1, []), by_round.get(2, []), by_round.get(3, []))
        for msg in msgs
        if msg.agent_pseudonym == "Agent A"
    ]
    for msg in agent_a_messages:
        assert "error" not in msg.content.lower()

    # Chairman synthesis ran
    assert len(by_round[0]) == 1
