import uuid
from datetime import datetime

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class SessionCreate(BaseModel):
    prompt: str


# ---------------------------------------------------------------------------
# Message schemas
# ---------------------------------------------------------------------------


class MessageResponse(BaseModel):
    """Message shape returned during and after deliberation — role/provider hidden."""

    id: uuid.UUID
    round_number: int
    agent_pseudonym: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageReveal(MessageResponse):
    """Extends MessageResponse with the fields revealed after deliberation ends."""

    agent_role: str
    agent_provider: str


# ---------------------------------------------------------------------------
# Session schemas
# ---------------------------------------------------------------------------


class SessionResponse(BaseModel):
    id: uuid.UUID
    prompt: str
    status: str
    final_decision: str | None
    created_at: datetime
    messages: list[MessageResponse]

    model_config = {"from_attributes": True}


class SessionReveal(SessionResponse):
    """Full session with agent identities revealed — returned after deliberation completes."""

    messages: list[MessageReveal]  # type: ignore[assignment]  # intentional narrowing
