"""Unit tests for Pydantic request/response schemas.

No database or API calls — pure validation logic.
"""

import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from backend.app.models.schemas import MessageResponse, MessageReveal, SessionCreate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW = datetime.now(tz=timezone.utc)

_MESSAGE_BASE = {
    "id": uuid.uuid4(),
    "round_number": 1,
    "agent_pseudonym": "Agent A",
    "content": "Here is my position.",
    "created_at": _NOW,
}


# ---------------------------------------------------------------------------
# SessionCreate
# ---------------------------------------------------------------------------


def test_session_create_valid():
    sc = SessionCreate(prompt="Is AI beneficial to society?")
    assert sc.prompt == "Is AI beneficial to society?"


def test_session_create_empty_prompt():
    # Empty string is still a valid str — no validator rejects it yet
    sc = SessionCreate(prompt="")
    assert sc.prompt == ""


def test_session_create_missing_prompt():
    with pytest.raises(ValidationError):
        SessionCreate()  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# MessageResponse — anonymization contract
# ---------------------------------------------------------------------------


def test_message_response_excludes_role_and_provider():
    msg = MessageResponse(**_MESSAGE_BASE)
    fields = msg.model_fields_set | set(msg.model_dump().keys())
    assert "agent_role" not in fields
    assert "agent_provider" not in fields


# ---------------------------------------------------------------------------
# MessageReveal — post-deliberation reveal contract
# ---------------------------------------------------------------------------


def test_message_reveal_includes_role_and_provider():
    msg = MessageReveal(
        **_MESSAGE_BASE,
        agent_role="Devil's Advocate",
        agent_provider="openai",
    )
    assert msg.agent_role == "Devil's Advocate"
    assert msg.agent_provider == "openai"
